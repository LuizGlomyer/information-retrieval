# ── Build Stage ──────────────────────────────────────────────
FROM node:20-slim AS build

WORKDIR /app

# Recebe a URL da API como argumento no build e define como variável de ambiente
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Copia dependências primeiro (cache de layer)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copia o restante do código e executa o build de produção
COPY frontend/ ./
RUN npm run build

# ── Serve Stage (Nginx Alpine para máxima performance e leveza) ────────────────
FROM nginx:alpine

# Copia os assets estáticos gerados no build
COPY --from=build /app/dist /usr/share/nginx/html

# Copia a configuração customizada do Nginx para suportar SPA routing
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8090

CMD ["nginx", "-g", "daemon off;"]
