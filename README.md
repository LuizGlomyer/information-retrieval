# Game Information Retrieval Lab

An advanced, playground-driven Information Retrieval system over a structured English-language game catalog. The project compares lexical and neural ranking models: **BM25**, **SVM (TF-IDF + Cosine Similarity)**, and **BERT Cross-Encoder**.

---

## 🚀 Setup & Installation

### 1. Download the Dataset
The project uses a structured game catalog dataset. Download and place it in the correct directory:

1. Download the zip dataset from Kaggle:
   ```bash
   curl -L -o igdb-dataset-for-data-mining-projects.zip https://www.kaggle.com/api/v1/datasets/download/emirshn/igdb-dataset-for-data-mining-projects
   ```
2. Unzip the file:
   ```bash
   unzip igdb-dataset-for-data-mining-projects.zip
   ```
3. Create the `ingestion` folder if it doesn't exist and move/rename the CSV file there:
   ```bash
   mkdir -p ingestion
   mv game_dataset_cleaned.csv ingestion/game_dataset_cleaned.csv
   ```

---

## 🐳 Running with Docker (Recommended)

Everything has been dockerized and optimized. The build process is optimized with `.dockerignore` to skip large directories (`node_modules`, `.venv`), and uses `python:3.14-rc-slim`.

### Startup
Simply run:
```bash
docker compose up --build
```

#### What happens automatically:
1. **Elasticsearch** starts up and runs its health check.
2. **Backend (FastAPI)** starts and connects to Elasticsearch. On startup, it checks if the indices (`games_bm25`, `games_svm`) already have data. If not, it reads the CSV at `ingestion/game_dataset_cleaned.csv` and ingests all **232,595** games automatically.
3. **Frontend (Vite)** starts up in hot-reload mode and connects to the backend API.

### Customizing Ports
You can change the exposed ports for any service by editing the central configuration file [`.env`](file:///.env) at the root:
```env
ELASTICSEARCH_HOST_PORT=9200
KIBANA_PORT=5601
BACKEND_PORT=8080
FRONTEND_PORT=8090
```

---

## 💻 Running Locally (Manual Dev Mode)

If you prefer to run services manually on your host machine:

### Prerequisites
- Python >= 3.14
- Node.js >= 20
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Elasticsearch running locally on `localhost:9200`

### 1. Backend Startup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies and start the FastAPI dev server:
   ```bash
   uv sync
   make run  # Runs uvicorn with hot-reload
   ```

### 2. Frontend Startup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies and start the Vite dev server:
   ```bash
   npm install
   npm run dev
   ```
3. Open `http://localhost:8090` in your browser.