"""
Application configuration and constants.
Centralize all settings for Elasticsearch connection and API limits.
"""

# Elasticsearch Configuration
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200

# Search Limits
DEFAULT_RESULT_SIZE = 5
MAX_RESULT_SIZE = 100
MIN_RESULT_SIZE = 1

# Supported fields for searching
SEARCHABLE_FIELDS = [
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

# ============================================================================
# TF-IDF (VECTOR SPACE MODEL - SALTON 1971) - PAINLESS SCRIPT
# ============================================================================
#
# Implements TF-IDF scoring inside Elasticsearch using Painless script.
# This script is used for SVM (Support Vector Model) ranking algorithm.
#
# FORMULA COMPONENTS:
# 1. TF (Term Frequency):
#    tf = √(freq)
#    - Raiz quadrada da frequência do termo no documento
#    - Suaviza o impacto de repetições
#
# 2. IDF (Inverse Document Frequency):
#    idf = log((docCount + 1) / (docFreq + 1)) + 1
#    - docCount = total de documentos
#    - docFreq = documentos que contêm o termo
#    - +1s evitam divisão por zero e log de zero
#
# 3. Norm (Normalização):
#    norm = 1 / √(length)
#    - length = número de termos no campo
#    - Normaliza por tamanho do documento
#
# 4. Score Final:
#    score = query.boost × tf × idf × norm
#
# REFERENCE: Teacher's indexa.py and buscaVSM.py
#
TFIDF_SCRIPT_SOURCE = """
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

# ============================================================================
# INDEX CONFIGURATIONS
# ============================================================================

# BM25 Index Configuration (Default Elasticsearch similarity)
BM25_INDEX_NAME = "games_bm25"
BM25_INDEX_CONFIG = {
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
        }
    },
}

# SVM (TF-IDF) Index Configuration with Scripted Similarity
SVM_INDEX_NAME = "games_svm"
SVM_INDEX_CONFIG = {
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
                "script": {"source": TFIDF_SCRIPT_SOURCE},
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
