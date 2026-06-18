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
    name: "SVM",
    shortName: "SVM",
    family: "lexical",
    tagline: "Support Vector Machine ranking",
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
    "P@1": 0.62, "P@5": 0.54, "P@10": 0.48,
    R: 0.41, MAP: 0.46, F1: 0.49,
    "NDCG@1": 0.62, "NDCG@5": 0.58, "NDCG@10": 0.55,
  },
  bm25_hybrid: {
    "P@1": 0.84, "P@5": 0.74, "P@10": 0.66,
    R: 0.65, MAP: 0.71, F1: 0.71,
    "NDCG@1": 0.84, "NDCG@5": 0.79, "NDCG@10": 0.75,
  },
  bert: {
    "P@1": 0.74, "P@5": 0.65, "P@10": 0.59,
    R: 0.55, MAP: 0.60, F1: 0.62,
    "NDCG@1": 0.74, "NDCG@5": 0.70, "NDCG@10": 0.67,
  },
  svm: {
    "P@1": 0.71, "P@5": 0.61, "P@10": 0.55,
    R: 0.48, MAP: 0.55, F1: 0.57,
    "NDCG@1": 0.71, "NDCG@5": 0.66, "NDCG@10": 0.62,
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
    title: "Vector Space Model — SVM",
    desc: "Scripted Similarity vector space model based on TF-IDF term frequency and cosine similarity. It ranks documents using custom similarity scoring directly inside Elasticsearch.",
    output: "Latency: ~110 ms",
  },
  {
    n: "05",
    title: "Neural reranking — BERT",
    desc: "Cross-encoder reads (query, document) jointly. Fine-tuned variant adapts to gaming vocabulary and editorial relevance labels.",
    output: "Latency: ~480 ms",
  },
  {
    n: "06",
    title: "Evaluation harness",
    desc: "Each model is scored on the same labeled query set across nine IR metrics. Results are versioned per experiment.",
    output: "9 metrics · 4 models",
  },
];
