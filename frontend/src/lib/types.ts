// Domain types — kept aligned with backend AGENTS.md so swapping mock for real API is trivial.

export type ModelId =
  | "bm25"
  | "bm25_weighted"
  | "bm25_weighted_embeddings"
  | "bert"
  | "bert_finetuned";

export interface ModelMeta {
  id: ModelId;
  name: string;
  shortName: string;
  family: "lexical" | "neural";
  tagline: string;
  description: string;
  techniques: string[];
  status: "stable" | "experimental" | "planned";
}

export interface MetricScores {
  "P@1": number;
  "P@5": number;
  "P@10": number;
  R: number;
  MAP: number;
  F1: number;
  "NDCG@1": number;
  "NDCG@5": number;
  "NDCG@10": number;
}

export type MetricKey = keyof MetricScores;

export interface GameResult {
  id: string;
  name: string;
  summary: string;
  cover: string;
  rating: number;
  release_date: string;
  genres: string[];
  platforms: string[];
  themes: string[];
}

export interface RankedResult extends GameResult {
  score: number;
  rank: number;
  algorithm: ModelId;
}

export interface AlgorithmResult {
  results: RankedResult[];
  total: number;
  execution_time_ms: number;
}

export type MultiAlgorithmSearchResponse = Partial<Record<ModelId, AlgorithmResult>>;

export interface SearchRequest {
  query_text: string;
  models: ModelId[];
  size?: number;
}
