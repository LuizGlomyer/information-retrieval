"""
Index Manager for creating and managing Elasticsearch indices.
Handles creation and data ingestion for both BM25 and SVM (TF-IDF) indices.
"""

import csv
import ast
import time
from pathlib import Path
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import BadRequestError
from config import (
    BM25_INDEX_NAME,
    BM25_INDEX_CONFIG,
    SVM_INDEX_NAME,
    SVM_INDEX_CONFIG,
)
from .embedding_service import EmbeddingService, format_semantic_content
from tqdm import tqdm


class BulkIndexingService:
    """
    Helper that batches BM25 embedding generation and Elasticsearch bulk actions.

    This class keeps ingestion state in instance fields instead of nested
    local functions. It is used by IndexManager.ingest_data to flush Elasticsearch
    actions in chunks and to generate embeddings in batch.
    """

    def __init__(
        self,
        es_client: Elasticsearch,
        bm25_index_name: str,
        svm_index_name: str,
        ingest_bm25: bool,
        ingest_svm: bool,
        batch_size: int = 256,
    ):
        self._es_client = es_client
        self._bm25_index_name = bm25_index_name
        self._svm_index_name = svm_index_name
        self.ingest_bm25 = ingest_bm25
        self.ingest_svm = ingest_svm
        self.batch_size = batch_size
        self._pending_actions = []
        self._pending_docs = []
        self._pending_texts = []
        self.doc_count = 0
        self._embedding_service = EmbeddingService() if ingest_bm25 else None

    def add_document(self, doc, semantic_text=None):
        if self.ingest_svm:
            self._pending_actions.append(
                {
                    "_index": self._svm_index_name,
                    "_id": doc["id"],
                    "_source": doc.copy(),
                }
            )

        if self.ingest_bm25:
            if semantic_text is None:
                raise ValueError("semantic_text is required for BM25 ingestion")
            self._pending_docs.append(doc)
            self._pending_texts.append(semantic_text)

        self.doc_count += 1
        self._maybe_flush()

    def finalize(self):
        if self.ingest_bm25:
            self._flush_embeddings()
        self._flush_actions()
        return self.doc_count

    def _maybe_flush(self):
        if self.ingest_bm25 and len(self._pending_docs) >= self.batch_size:
            self._flush_embeddings()

        if len(self._pending_actions) >= self.batch_size * 2:
            self._flush_actions()

    def _flush_embeddings(self):
        if not self._pending_docs:
            return

        embeddings = self._embedding_service.embed_batch(self._pending_texts)
        for doc, embedding in zip(self._pending_docs, embeddings):
            doc["semantic_embedding"] = embedding
            self._pending_actions.append(
                {
                    "_index": self._bm25_index_name,
                    "_id": doc["id"],
                    "_source": doc,
                }
            )

        self._pending_docs = []
        self._pending_texts = []

    def _flush_actions(self):
        if not self._pending_actions:
            return

        helpers.bulk(self._es_client, self._pending_actions)
        self._pending_actions = []


class IndexManager:
    """
    Manages Elasticsearch indices for multi-algorithm search.
    Handles creation and data ingestion for:
    - BM25 index (standard Elasticsearch similarity)
    - SVM index (TF-IDF via Scripted Similarity)
    """

    @staticmethod
    def _parse_list(value):
        """Parse string representation of list."""
        try:
            return ast.literal_eval(value) if value else []
        except ValueError, SyntaxError:
            return []

    @staticmethod
    def _parse_float(value):
        """Parse float value with None fallback."""
        try:
            return float(value) if value else None
        except ValueError, TypeError:
            return None

    @staticmethod
    def _get_ingest_status(es_client: Elasticsearch):
        """
        Check whether BM25 and SVM indices need ingestion.

        Returns:
            Tuple[bool, bool, int, int]: ingest_bm25, ingest_svm, bm25_count, svm_count
        """
        bm25_count = es_client.count(index=BM25_INDEX_NAME)["count"]
        svm_count = es_client.count(index=SVM_INDEX_NAME)["count"]
        return bm25_count == 0, svm_count == 0, bm25_count, svm_count

    @staticmethod
    def _log_ingest_status(
        ingest_bm25: bool,
        ingest_svm: bool,
        bm25_count: int,
        svm_count: int,
    ) -> bool:
        """
        Print ingestion status and return whether ingestion is required.
        """
        if not ingest_bm25 and not ingest_svm:
            print("✓ Both indices already contain data")
            print(f"  - {BM25_INDEX_NAME}: {bm25_count} documents")
            print(f"  - {SVM_INDEX_NAME}: {svm_count} documents")
            print("=" * 70)
            return False

        if not ingest_bm25:
            print(f"✓ BM25 index already populated ({bm25_count} documents)")
        if not ingest_svm:
            print(f"✓ SVM index already populated ({svm_count} documents)")
        if ingest_bm25 and ingest_svm:
            print("✓ Both BM25 and SVM need ingestion")
        elif ingest_bm25:
            print("✓ Only BM25 needs ingestion")
        elif ingest_svm:
            print("✓ Only SVM needs ingestion")

        return True

    @staticmethod
    def create_index_if_not_exists(
        es_client: Elasticsearch, index_name: str, index_config: dict
    ) -> bool:
        """
        Create index if it doesn't exist.

        Args:
            es_client: Elasticsearch client
            index_name: Name of the index to create
            index_config: Index configuration (settings + mappings)

        Returns:
            True if index created or already exists, False on error
        """
        try:
            if es_client.indices.exists(index=index_name):
                print(f"✓ Index '{index_name}' already exists")
                return True

            es_client.indices.create(index=index_name, body=index_config)
            print(f"✓ Index '{index_name}' created successfully")
            return True

        except BadRequestError as e:
            print(f"⚠ BadRequestError for index '{index_name}': {e}")
            return False
        except Exception as e:
            print(f"❌ Error creating index '{index_name}': {e}")
            return False

    @staticmethod
    def initialize_indices(es_client: Elasticsearch) -> bool:
        """
        Initialize both BM25 and SVM indices and ingest data.

        Creates:
        1. BM25 index with standard similarity (games)
        2. SVM index with TF-IDF scripted similarity (games_svm)
        3. Ingests data from CSV file into both indices

        Args:
            es_client: Elasticsearch client

        Returns:
            True if both indices created/exist and data ingested, False if error
        """
        print("\n" + "=" * 70)
        print("INITIALIZING ELASTICSEARCH INDICES")
        print("=" * 70)

        # Create BM25 index
        print(f"\n1. Setting up BM25 Index: '{BM25_INDEX_NAME}'")
        print("   Similarity: Default (BM25)")
        bm25_ok = IndexManager.create_index_if_not_exists(
            es_client=es_client,
            index_name=BM25_INDEX_NAME,
            index_config=BM25_INDEX_CONFIG,
        )

        # Create SVM index
        print(f"\n2. Setting up SVM Index: '{SVM_INDEX_NAME}'")
        print("   Similarity: Scripted (TF-IDF - Vector Space Model)")
        print("   Formula: score = query.boost × √(freq) × idf × (1/√(length))")
        svm_ok = IndexManager.create_index_if_not_exists(
            es_client=es_client,
            index_name=SVM_INDEX_NAME,
            index_config=SVM_INDEX_CONFIG,
        )

        if not (bm25_ok and svm_ok):
            print("❌ FAILED TO INITIALIZE INDICES")
            print("=" * 70)
            return False

        print("\n" + "=" * 70)
        print("✓ INDICES INITIALIZED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nBM25 Index:  {BM25_INDEX_NAME}")
        print(f"SVM Index:   {SVM_INDEX_NAME}")

        # Try multiple locations for the CSV file
        # Order: Docker volume mount first, then local dev paths
        csv_candidates = [
            "/app/data/game_dataset_cleaned.csv",    # Docker volume mount
            "../ingestion/game_dataset_cleaned.csv", # repo/ingestion/ (run from backend/)
            "../game_dataset_cleaned.csv",           # repo root (run from backend/)
            "ingestion/game_dataset_cleaned.csv",    # repo/ingestion/ (run from repo root)
            "game_dataset_cleaned.csv",              # current dir
        ]
        csv_file = next(
            (p for p in csv_candidates if Path(p).exists()), csv_candidates[0]
        )
        ingest_ok = IndexManager.ingest_data(es_client, csv_file)

        return ingest_ok

    @staticmethod
    def ingest_data(es_client: Elasticsearch, csv_file_path: str) -> bool:
        """
        Ingest data from CSV file into both BM25 and SVM indices.

        Reads game dataset from CSV and bulk indexes all documents to both indices.

        Args:
            es_client: Elasticsearch client
            csv_file_path: Path to CSV file with game data

        Returns:
            True if ingestion successful, False if error or no data found
        """
        try:
            # Verify file exists
            csv_path = Path(csv_file_path)
            print(csv_path.resolve())
            if not csv_path.exists():
                print(f"\n⚠ CSV file not found: {csv_file_path}")
                print("   Data will need to be ingested separately")
                return True  # Return True to not block app startup

            print("\n" + "=" * 70)
            print("INGESTING DATA INTO INDICES")
            print("=" * 70)
            print(f"Reading from: {csv_file_path}\n")

            ingest_bm25, ingest_svm, bm25_count, svm_count = (
                IndexManager._get_ingest_status(es_client)
            )

            if not IndexManager._log_ingest_status(
                ingest_bm25,
                ingest_svm,
                bm25_count,
                svm_count,
            ):
                return True

            indexer = BulkIndexingService(
                es_client=es_client,
                bm25_index_name=BM25_INDEX_NAME,
                svm_index_name=SVM_INDEX_NAME,
                ingest_bm25=ingest_bm25,
                ingest_svm=ingest_svm,
            )

            # Read and count CSV rows for progress reporting
            with open(csv_path, encoding="utf-8") as f:
                total_rows = sum(1 for _ in f) - 1

            if total_rows <= 0:
                print("⚠ No documents found in CSV file")
                print("=" * 70)
                return False

            print(f"Total documents to index: {total_rows}\n")
            ingestion_start = time.perf_counter()

            desc_label = "Embedding" if ingest_bm25 else "Indexing"
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in tqdm(
                    reader,
                    total=total_rows,
                    unit="doc",
                    desc=desc_label,
                    ncols=80,
                ):
                    base_doc = {
                        "id": row["id"],
                        "name": row["name"],
                        "summary": row["summary"],
                        "category": row["category"],
                        "release_date": row["release_date"] or None,
                        "rating": IndexManager._parse_float(row["rating"]),
                        "aggregated_rating": IndexManager._parse_float(
                            row.get("aggregated_rating")
                        ),
                        "genres": IndexManager._parse_list(row["genres"]),
                        "themes": IndexManager._parse_list(row["themes"]),
                        "keywords": IndexManager._parse_list(row["keywords"]),
                        "platforms": IndexManager._parse_list(row.get("platforms")),
                        "game_modes": IndexManager._parse_list(row.get("game_modes")),
                        "player_perspectives": IndexManager._parse_list(
                            row.get("player_perspectives")
                        ),
                        "cover_url": row.get("cover_url"),
                        "screenshot_urls": IndexManager._parse_list(
                            row.get("screenshot_urls")
                        ),
                        "artwork_urls": IndexManager._parse_list(
                            row.get("artwork_urls")
                        ),
                    }

                    semantic_text = None
                    if ingest_bm25:
                        semantic_text = format_semantic_content(
                            name=row["name"],
                            summary=row["summary"],
                            genres=IndexManager._parse_list(row["genres"]),
                            themes=IndexManager._parse_list(row["themes"]),
                            keywords=IndexManager._parse_list(row["keywords"]),
                        )

                    indexer.add_document(base_doc, semantic_text=semantic_text)

            doc_count = indexer.finalize()
            ingestion_elapsed = time.perf_counter() - ingestion_start
            print(f"\n✓ Data ingestion completed in {ingestion_elapsed:.2f}s")

            # Refresh indices after bulk ingestion
            if doc_count > 0:
                if ingest_bm25:
                    es_client.indices.refresh(index=BM25_INDEX_NAME)
                if ingest_svm:
                    es_client.indices.refresh(index=SVM_INDEX_NAME)

                print(
                    f"✓ Successfully indexed {doc_count} documents to {'both indices' if ingest_bm25 and ingest_svm else BM25_INDEX_NAME if ingest_bm25 else SVM_INDEX_NAME}"
                )
                if ingest_bm25:
                    print(f"  - {BM25_INDEX_NAME} (BM25 with semantic embeddings)")
                if ingest_svm:
                    print(f"  - {SVM_INDEX_NAME} (TF-IDF)")
                print("=" * 70)
                return True
            else:
                print("⚠ No documents found in CSV file")
                print("=" * 70)
                return False

        except FileNotFoundError:
            print(f"\n⚠ CSV file not found at: {csv_file_path}")
            print("   Data will need to be ingested separately")
            # Don't block app startup
            return True
        except Exception as e:
            print(f"\n❌ Error during ingestion: {e}")
            print("=" * 70)
            return False
