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

# 🔧 Mapping mais completo (inclui frontend + IR)
mapping = {
    "settings": {
        "analysis": {
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

            "category": {"type": "keyword"},
            "genres": {"type": "keyword"},
            "themes": {"type": "keyword"},
            "keywords": {"type": "keyword"},

            "release_date": {"type": "date"},

            "rating": {"type": "float"},
            "aggregated_rating": {"type": "float"},

            "platforms": {"type": "keyword"},
            "game_modes": {"type": "keyword"},
            "player_perspectives": {"type": "keyword"},

            # 🎨 FRONTEND (importante agora)
            "cover_url": {"type": "keyword"},
            "screenshot_urls": {"type": "keyword"},
            "artwork_urls": {"type": "keyword"}
        }
    }
}

# 🔒 Cria índice só se não existir
if not es.indices.exists(index=INDEX_NAME):
    es.indices.create(index=INDEX_NAME, body=mapping)

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
            "_id": row["id"],  # 🔥 garante idempotência
            "_source": doc
        })

# 🚀 Bulk indexing
helpers.bulk(es, actions)

print("Indexação concluída com sucesso!")