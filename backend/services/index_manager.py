"""
Index Manager for creating and managing Elasticsearch indices.
Handles creation and data ingestion for both BM25 and SVM (TF-IDF) indices.
"""

import csv
import ast
from pathlib import Path
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import BadRequestError
from config import (
    BM25_INDEX_NAME,
    BM25_INDEX_CONFIG,
    SVM_INDEX_NAME,
    SVM_INDEX_CONFIG,
)


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
        except:
            return []

    @staticmethod
    def _parse_float(value):
        """Parse float value with None fallback."""
        try:
            return float(value) if value else None
        except:
            return None

    @staticmethod
    def create_index_if_not_exists(
        es_client: Elasticsearch,
        index_name: str,
        index_config: dict
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
            index_config=BM25_INDEX_CONFIG
        )
        
        # Create SVM index
        print(f"\n2. Setting up SVM Index: '{SVM_INDEX_NAME}'")
        print("   Similarity: Scripted (TF-IDF - Vector Space Model)")
        print("   Formula: score = query.boost × √(freq) × idf × (1/√(length))")
        svm_ok = IndexManager.create_index_if_not_exists(
            es_client=es_client,
            index_name=SVM_INDEX_NAME,
            index_config=SVM_INDEX_CONFIG
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
        
        # Ingest data
        csv_file = "../game_dataset_cleaned.csv" # root folder of repository
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
            
            actions = []
            doc_count = 0
            
            # Check if both indices already have data
            bm25_count = es_client.count(index=BM25_INDEX_NAME)["count"]
            svm_count = es_client.count(index=SVM_INDEX_NAME)["count"]
            
            if bm25_count > 0 and svm_count > 0:
                print(f"✓ Both indices already contain data")
                print(f"  - {BM25_INDEX_NAME}: {bm25_count} documents")
                print(f"  - {SVM_INDEX_NAME}: {svm_count} documents")
                print("=" * 70)
                return True
            
            # Read and parse CSV
            with open(csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    doc = {
                        "id": row["id"],
                        "name": row["name"],
                        "summary": row["summary"],
                        "category": row["category"],
                        "release_date": row["release_date"] or None,
                        "rating": IndexManager._parse_float(row["rating"]),
                        "aggregated_rating": IndexManager._parse_float(row.get("aggregated_rating")),
                        "genres": IndexManager._parse_list(row["genres"]),
                        "themes": IndexManager._parse_list(row["themes"]),
                        "keywords": IndexManager._parse_list(row["keywords"]),
                        "platforms": IndexManager._parse_list(row.get("platforms")),
                        "game_modes": IndexManager._parse_list(row.get("game_modes")),
                        "player_perspectives": IndexManager._parse_list(row.get("player_perspectives")),
                        "cover_url": row.get("cover_url"),
                        "screenshot_urls": IndexManager._parse_list(row.get("screenshot_urls")),
                        "artwork_urls": IndexManager._parse_list(row.get("artwork_urls"))
                    }
                    
                    # Index same document to both BM25 and SVM indices
                    actions.append({
                        "_index": BM25_INDEX_NAME,
                        "_id": row["id"],
                        "_source": doc
                    })
                    actions.append({
                        "_index": SVM_INDEX_NAME,
                        "_id": row["id"],
                        "_source": doc
                    })
                    
                    doc_count += 1
            
            # Bulk index to both indices
            if doc_count > 0:
                helpers.bulk(es_client, actions)
                es_client.indices.refresh(index=BM25_INDEX_NAME)
                es_client.indices.refresh(index=SVM_INDEX_NAME)
                
                print(f"✓ Successfully indexed {doc_count} documents to both indices")
                print(f"  - {BM25_INDEX_NAME} (BM25)")
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
            return True  # Don't block app startup
        except Exception as e:
            print(f"\n❌ Error during ingestion: {e}")
            print("=" * 70)
            return False

