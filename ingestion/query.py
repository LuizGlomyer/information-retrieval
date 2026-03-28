from elasticsearch import Elasticsearch

# Conexão
es = Elasticsearch("http://localhost:9200")

# Query simples por nome
query = {
    "match": {
        "name": "Super Mario"
    }
}

# Executa busca
response = es.search(
    index="games",
    query=query,
    size=10
)

# Exibe resultados
print("Resultados:\n")

for hit in response["hits"]["hits"]:
    source = hit["_source"]
    print(f"ID: {hit['_id']}")
    print(f"Nome: {source.get('name')}")
    print(f"Rating: {source.get('rating')}")
    print(f"Score: {hit['_score']}")
    print("-" * 40)