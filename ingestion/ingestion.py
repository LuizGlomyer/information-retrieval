import csv
import ast
from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(
    "http://localhost:9200",
    verify_certs=False,
    request_timeout=30
)

INDEX_NAME = "games"

print(es.info())

mapping = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "normalizer": {
                "lowercase_normalizer": {
                    "type": "custom",
                    "filter": ["lowercase"]
                }
            },
            "analyzer": {
                "default": {
                    "type": "standard"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},

            "name": {
                "type": "text",
                "fields": {
                    "keyword": {"type": "keyword"}
                }
            },

            "summary": {"type": "text"},

            "category": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "genres": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "themes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "keywords": {"type": "keyword", "normalizer": "lowercase_normalizer"},

            "release_date": {"type": "date"},

            "rating": {"type": "float"},
            "aggregated_rating": {"type": "float"},

            "platforms": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "game_modes": {"type": "keyword", "normalizer": "lowercase_normalizer"},
            "player_perspectives": {"type": "keyword", "normalizer": "lowercase_normalizer"},

            # 🎨 FRONTEND
            "cover_url": {"type": "keyword"},
            "screenshot_urls": {"type": "keyword"},
            "artwork_urls": {"type": "keyword"}
        }
    }
}

if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)
    print(f"Deleted existing index '{INDEX_NAME}'")

es.indices.create(index=INDEX_NAME, body=mapping)
print(f"Created index '{INDEX_NAME}' with normalizer mapping")

def parse_list(value):
    try:
        return ast.literal_eval(value) if value else []
    except:
        return []

def parse_float(value):
    try:
        return float(value) if value else None
    except:
        return None

actions = []

with open("game_dataset_cleaned.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        doc = {
            "id": row["id"],
            "name": row["name"],
            "summary": row["summary"],

            "category": row["category"],

            "release_date": row["release_date"] or None,

            "rating": parse_float(row["rating"]),
            "aggregated_rating": parse_float(row.get("aggregated_rating")),

            "genres": parse_list(row["genres"]),
            "themes": parse_list(row["themes"]),
            "keywords": parse_list(row["keywords"]),

            "platforms": parse_list(row.get("platforms")),
            "game_modes": parse_list(row.get("game_modes")),
            "player_perspectives": parse_list(row.get("player_perspectives")),

            # 🎨 FRONTEND
            "cover_url": row.get("cover_url"),
            "screenshot_urls": parse_list(row.get("screenshot_urls")),
            "artwork_urls": parse_list(row.get("artwork_urls"))
        }

        actions.append({
            "_index": INDEX_NAME,
            "_id": row["id"],
            "_source": doc
        })

# 🚀 Bulk indexing
helpers.bulk(es, actions)

print("Indexing completed successfully!")