.PHONY: run format lint

run:
	uvicorn main:app --reload --port 8080

format:
	uv ruff format .

lint:
	uv ruff check . --fix
