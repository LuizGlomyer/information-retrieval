import type { ModelMeta, MetricScores, MetricKey } from "./types";

export const MODELS: ModelMeta[] = [
  {
    id: "bm25",
    name: "BM25",
    shortName: "BM25",
    family: "lexical",
    tagline: "Native lexical baseline",
    description:
      "Elasticsearch's native ranking. Term frequency, inverse document frequency and length normalization on each searchable field.",
    techniques: ["TF-IDF", "Length norm", "Multi-match"],
    status: "stable",
  },
  {
    id: "bm25_hybrid",
    name: "BM25 Hybrid",
    shortName: "Hybrid",
    family: "neural",
    tagline: "Lexical & semantic search",
    description:
      "Combines lexical BM25 matching with dense vector embedding similarity for a rich, hybrid relevance ranking.",
    techniques: ["BM25", "BGE Embeddings", "Hybrid fusion"],
    status: "stable",
  },
  {
    id: "bert",
    name: "BERT",
    shortName: "BERT",
    family: "neural",
    tagline: "Dense vector retrieval",
    description:
      "Dense retrieval using pre-trained BGE embeddings. Computes cosine similarity between query and document vectors.",
    techniques: ["BGE Embeddings", "Dense Vector", "Cosine similarity"],
    status: "stable",
  },
  {
    id: "svm",
    name: "VSM",
    shortName: "VSM",
    family: "lexical",
    tagline: "Vector Space Model ranking",
    description:
      "Scripted Similarity vector space model based on TF-IDF term frequency and cosine similarity.",
    techniques: ["TF-IDF", "Cosine similarity", "Vector space"],
    status: "stable",
  },
];

export const ALL_METRIC_KEYS: MetricKey[] = [
  "P@1",
  "P@5",
  "P@10",
  "R",
  "MAP",
  "F1",
  "NDCG@1",
  "NDCG@5",
  "NDCG@10",
];

// Demo metrics — populated from backend when available.
export const MODEL_METRICS: Record<string, MetricScores> = {
  bm25: {
    "P@1": 0.8500, "P@5": 0.8700, "P@10": 0.8450,
    R: 0.5250, MAP: 0.4855, F1: 0.6235,
    "NDCG@1": 0.8000, "NDCG@5": 0.7671, "NDCG@10": 0.7723,
  },
  bm25_hybrid: {
    "P@1": 0.8500, "P@5": 0.8600, "P@10": 0.8350,
    R: 0.5164, MAP: 0.4710, F1: 0.6144,
    "NDCG@1": 0.8000, "NDCG@5": 0.7795, "NDCG@10": 0.7597,
  },
  bert: {
    "P@1": 0.4500, "P@5": 0.4400, "P@10": 0.4250,
    R: 0.2617, MAP: 0.1825, F1: 0.3105,
    "NDCG@1": 0.3500, "NDCG@5": 0.3511, "NDCG@10": 0.3645,
  },
  svm: {
    "P@1": 0.8000, "P@5": 0.8100, "P@10": 0.7850,
    R: 0.4885, MAP: 0.4451, F1: 0.5802,
    "NDCG@1": 0.7333, "NDCG@5": 0.6798, "NDCG@10": 0.6982,
  },
};

export const RERANK_MODEL_METRICS: Record<string, MetricScores> = {
  bm25: {
    "P@1": 1.0000, "P@5": 0.9600, "P@10": 0.8450,
    R: 0.5250, MAP: 0.5125, F1: 0.6235,
    "NDCG@1": 0.9000, "NDCG@5": 0.8533, "NDCG@10": 0.8011,
  },
  bm25_hybrid: {
    "P@1": 1.0000, "P@5": 0.9600, "P@10": 0.8350,
    R: 0.5164, MAP: 0.5047, F1: 0.6144,
    "NDCG@1": 0.9000, "NDCG@5": 0.8531, "NDCG@10": 0.7830,
  },
  bert: {
    "P@1": 0.7000, "P@5": 0.5700, "P@10": 0.4250,
    R: 0.2617, MAP: 0.2302, F1: 0.3105,
    "NDCG@1": 0.6167, "NDCG@5": 0.5189, "NDCG@10": 0.4324,
  },
  svm: {
    "P@1": 0.9500, "P@5": 0.8900, "P@10": 0.7850,
    R: 0.4885, MAP: 0.4741, F1: 0.5802,
    "NDCG@1": 0.8333, "NDCG@5": 0.7728, "NDCG@10": 0.7335,
  },
};


export const PIPELINE_STEPS = [
  {
    n: "01",
    title: "Corpus ingestion",
    desc: "Game records normalized and indexed into Elasticsearch with a typed mapping (name, summary, genres, themes, platforms, ratings).",
    output: "232,595 documents · 11 fields",
  },
  {
    n: "02",
    title: "Text preprocessing",
    desc: "Lowercasing, whitespace tokenization, English stopword pruning. Future work: lemmatization and named-entity tagging for franchises.",
    output: "Avg. 84 tokens / doc",
  },
  {
    n: "03",
    title: "Lexical retrieval — BM25",
    desc: "Multi-match queries with optional field weights. Captures exact and morphological matches; serves as the strong baseline.",
    output: "Latency: ~120 ms",
  },
  {
    n: "04",
    title: "Vector Space Model — VSM",
    desc: "Scripted Similarity vector space model based on TF-IDF term frequency and cosine similarity. It ranks documents using custom similarity scoring directly inside Elasticsearch.",
    output: "Latency: ~110 ms",
  },
  {
    n: "05",
    title: "Neural reranking — BERT",
    desc: "Cross-encoder reads (query, document) jointly. Uses the pre-trained BAAI/bge-reranker-base model from Hugging Face.",
    output: "Latency: ~480 ms",
  },
  {
    n: "06",
    title: "Evaluation harness",
    desc: "Each model is scored on the same labeled query set across nine IR metrics. Results are versioned per experiment.",
    output: "9 metrics · 4 models",
  },
];
