"""
Application configuration and constants.
Centralize all settings for Elasticsearch connection and API limits.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """
    Configuration object for the backend.

    Loads environment variables from `backend/.env` and exposes
    configuration values through a single instance.
    """

    def __init__(self) -> None:
        # Elasticsearch Configuration — reads from env vars (Docker) or falls back to localhost
        self.ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
        self.ELASTICSEARCH_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))

        # Gemini Configuration — API key required for /search/generate-qrels
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        # Search Limits
        self.DEFAULT_RESULT_SIZE = 5
        self.MAX_RESULT_SIZE = 1000
        self.MIN_RESULT_SIZE = 1

        # Embedding model configuration for semantic search
        self.BM25_EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
        self.BM25_EMBEDDING_DIMENSION = 384

        # BM25_EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
        # BM25_EMBEDDING_DIMENSION = 768

        # Supported fields for searching
        self.SEARCHABLE_FIELDS = [
            "name",
            "summary",
            "keywords",
            "themes",
            "category",
            "genres",
            "platforms",
            "player_perspectives",
            "game_modes",
        ]

        self.DEFAULT_SEARCH_FIELD_WEIGHTS: List[Tuple[str, float]] = [
            ("name", 3.0),
            ("summary", 2.0),
            ("keywords", 1.5),
            ("themes", 1.0),
            ("genres", 1.0),
            ("category", 0.5),
            # ("player_perspectives", 0.5),
            ("game_modes", 0.15),
        ]

        self.TFIDF_SCRIPT_SOURCE = """
// TF-IDF Classic de Salton (1971) - Vector Space Model
// Parâmetros disponíveis em tempo de execução:
// - doc.freq: frequência do termo neste documento
// - doc.length: número de termos neste campo neste documento  
// - term.docFreq: documentos que contêm o termo
// - field.docCount: total de documentos no índice
// - query.boost: peso da consulta (padrão: 1.0)

// 1. TF (Term Frequency) - raiz quadrada
double tf = Math.sqrt(doc.freq);

// 2. IDF (Inverse Document Frequency)
double idf = Math.log((field.docCount + 1.0) / (term.docFreq + 1.0)) + 1.0;

// 3. Normalização pelo comprimento do documento
double norm = 1.0 / Math.sqrt(doc.length);

// 4. Score final: TF × IDF × normalização × query boost
return query.boost * tf * idf * norm;
"""

        self.BM25_INDEX_NAME = "games_bm25"
        self.BM25_INDEX_CONFIG: Dict[str, object] = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "normalizer": {
                        "lowercase_normalizer": {"type": "custom", "filter": ["lowercase"]}
                    },
                    "analyzer": {"default": {"type": "standard"}},
                },
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "summary": {"type": "text"},
                    "category": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "genres": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "themes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "keywords": {"type": "text"},
                    "release_date": {"type": "date"},
                    "rating": {"type": "float"},
                    "aggregated_rating": {"type": "float"},
                    "platforms": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "game_modes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "player_perspectives": {
                        "type": "keyword",
                        "normalizer": "lowercase_normalizer",
                    },
                    "cover_url": {"type": "keyword"},
                    "screenshot_urls": {"type": "keyword"},
                    "artwork_urls": {"type": "keyword"},
                    "semantic_text": {"type": "text", "index": False},
                    "semantic_embedding": {
                        "type": "dense_vector",
                        "dims": self.BM25_EMBEDDING_DIMENSION,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        }

        self.SVM_INDEX_NAME = "games_svm"
        self.SVM_INDEX_CONFIG: Dict[str, object] = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "normalizer": {
                        "lowercase_normalizer": {"type": "custom", "filter": ["lowercase"]}
                    },
                    "analyzer": {"default": {"type": "standard"}},
                },
                "similarity": {
                    "tfidf_salton": {
                        "type": "scripted",
                        "script": {"source": self.TFIDF_SCRIPT_SOURCE},
                    }
                },
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "similarity": "tfidf_salton",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "summary": {"type": "text", "similarity": "tfidf_salton"},
                    "category": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "genres": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "themes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "keywords": {"type": "text", "similarity": "tfidf_salton"},
                    "release_date": {"type": "date"},
                    "rating": {"type": "float"},
                    "aggregated_rating": {"type": "float"},
                    "platforms": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "game_modes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
                    "player_perspectives": {
                        "type": "keyword",
                        "normalizer": "lowercase_normalizer",
                    },
                    "cover_url": {"type": "keyword"},
                    "screenshot_urls": {"type": "keyword"},
                    "artwork_urls": {"type": "keyword"},
                }
            },
        }


config = Config()
