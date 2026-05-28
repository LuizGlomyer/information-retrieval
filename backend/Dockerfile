# ── Backend (FastAPI + uv) ────────────────────────────────────
FROM python:3.14-rc-slim

WORKDIR /app

# Instala uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copia arquivos de dependências primeiro (cache de layer)
COPY backend/pyproject.toml backend/uv.lock ./

# Instala dependências sem sync do projeto (só deps)
RUN uv sync --frozen --no-install-project

# Copia o código do backend
COPY backend/ ./

# Expõe a porta interna
EXPOSE 8080

# Entrypoint: sobe o servidor (a ingestão acontece automaticamente no startup)
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
