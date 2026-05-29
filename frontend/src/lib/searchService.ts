// Mock fallback: used for models not yet implemented in the backend (bert, bert_finetuned)

import { MOCK_GAMES } from "./mockData";
import type {
  AlgorithmResult,
  ModelId,
  MultiAlgorithmSearchResponse,
  RankedResult,
  SearchRequest,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8080";


// Only "bm25" and "svm" are real.
const BACKEND_MODEL_MAP: Partial<Record<ModelId, "bm25" | "svm">> = {
  bm25: "bm25",
  svm: "svm",
};

// ──────────────────────────────────────────────────────────────────────────────
// Backend API call
// ──────────────────────────────────────────────────────────────────────────────

interface BackendRankedResult {
  id: string;
  name: string;
  summary?: string;
  cover_url?: string;
  rating?: number;
  aggregated_rating?: number;
  release_date?: string;
  genres?: string[];
  themes?: string[];
  platforms?: string[];
  score: number;
  rank: number;
  algorithm: string;
}

interface BackendAlgorithmResult {
  results: BackendRankedResult[];
  total: number;
  execution_time_ms: number;
}

interface BackendSearchResponse {
  bm25: BackendAlgorithmResult;
  svm: BackendAlgorithmResult;
}

async function fetchFromBackend(
  queryText: string,
  size: number,
): Promise<BackendSearchResponse | null> {
  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query_text: queryText, size }),
      signal: AbortSignal.timeout(10_000),
    });
    if (!res.ok) return null;
    return (await res.json()) as BackendSearchResponse;
  } catch {
    return null;
  }
}

function mapBackendResult(
  r: BackendRankedResult,
  modelId: ModelId,
): RankedResult {
  return {
    id: r.id,
    name: r.name,
    summary: r.summary ?? "",
    cover: r.cover_url ?? "",
    rating: r.rating ?? r.aggregated_rating ?? 0,
    release_date: r.release_date ?? "",
    genres: r.genres ?? [],
    platforms: r.platforms ?? [],
    themes: r.themes ?? [],
    score: Math.round(r.score * 100) / 100,
    rank: r.rank,
    algorithm: modelId,
  };
}

// ──────────────────────────────────────────────────────────────────────────────
// Mock fallback (for models not yet in backend)
// ──────────────────────────────────────────────────────────────────────────────

const tokenize = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

const hash = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10_000) / 10_000;
};

interface ModelKnobs {
  lexical: number;
  semantic: number;
  scale: number;
  latencyMs: number;
}

const KNOBS: Record<ModelId, ModelKnobs> = {
  bm25: { lexical: 1.0, semantic: 0.1, scale: 9.5, latencyMs: 95 },
  svm: { lexical: 1.0, semantic: 0.2, scale: 12.0, latencyMs: 110 },
  bert: { lexical: 0.4, semantic: 1.0, scale: 0.94, latencyMs: 410 },
  bert_finetuned: { lexical: 0.45, semantic: 1.1, scale: 0.97, latencyMs: 460 },
};

const scoreGame = (
  query: string,
  game: (typeof MOCK_GAMES)[number],
  knobs: ModelKnobs,
  modelSalt: string,
) => {
  const qTokens = tokenize(query);
  if (qTokens.length === 0) return 0;
  const corpus = [
    game.name,
    game.summary,
    game.genres.join(" "),
    game.themes.join(" "),
    game.platforms.join(" "),
  ].join(" ");
  const dTokens = tokenize(corpus);
  const dSet = new Set(dTokens);
  let lex = 0;
  const nameTokens = new Set(tokenize(game.name));
  for (const t of qTokens) {
    if (nameTokens.has(t)) lex += 2.2;
    else if (dSet.has(t)) lex += 1.0;
  }
  lex = lex / Math.max(qTokens.length, 1);
  let sem = 0;
  for (const t of qTokens) {
    for (const dt of dSet) {
      if (dt !== t && dt.length >= 4 && t.length >= 4) {
        if (dt.startsWith(t.slice(0, 4)) || t.startsWith(dt.slice(0, 4))) {
          sem += 0.5;
          break;
        }
      }
    }
  }
  sem += game.rating / 200;
  const noise = (hash(modelSalt + game.id) - 0.5) * 0.3;
  const raw = knobs.lexical * lex + knobs.semantic * sem + noise;
  return Math.max(0, raw) * knobs.scale;
};

function runMockSearch(
  modelId: ModelId,
  queryText: string,
  size: number,
): AlgorithmResult {
  const knobs = KNOBS[modelId];
  const scored = MOCK_GAMES.map((g) => ({
    g,
    s: scoreGame(queryText, g, knobs, modelId),
  }))
    .filter((x) => x.s > 0.05)
    .sort((a, b) => b.s - a.s)
    .slice(0, size);

  const results: RankedResult[] = scored.map(({ g, s }, i) => ({
    ...g,
    score: Math.round(s * 100) / 100,
    rank: i + 1,
    algorithm: modelId,
  }));

  return {
    results,
    total: scored.length,
    execution_time_ms:
      knobs.latencyMs +
      Math.round((hash(modelId + queryText) - 0.5) * 30),
  };
}

// ──────────────────────────────────────────────────────────────────────────────
// Main entry point
// ──────────────────────────────────────────────────────────────────────────────

export async function executeSearch(
  req: SearchRequest,
): Promise<MultiAlgorithmSearchResponse> {
  const size = req.size ?? 6;

  // Determine which requested models map to the real backend
  const backendModels = req.models.filter((m) => BACKEND_MODEL_MAP[m] != null);
  const mockModels = req.models.filter((m) => BACKEND_MODEL_MAP[m] == null);

  const response: MultiAlgorithmSearchResponse = {};

  // Fetch from backend if any real model is requested
  let backendData: BackendSearchResponse | null = null;
  if (backendModels.length > 0) {
    backendData = await fetchFromBackend(req.query_text, size);
  }

  for (const modelId of req.models) {
    const backendKey = BACKEND_MODEL_MAP[modelId];

    if (backendKey && backendData) {
      // Map real backend response to frontend shape
      const algo = backendData[backendKey];
      response[modelId] = {
        results: algo.results.map((r) => mapBackendResult(r, modelId)),
        total: algo.total,
        execution_time_ms: algo.execution_time_ms,
      };
    } else if (backendKey && !backendData) {
      // Backend unavailable — fall back to mock for this model too
      response[modelId] = runMockSearch(modelId, req.query_text, size);
    } else {
      // Mock-only model (bert, bert_finetuned)
      await new Promise((r) => setTimeout(r, 280));
      response[modelId] = runMockSearch(modelId, req.query_text, size);
    }
  }

  // Ensure mock models have a small artificial delay only once
  void mockModels; // already handled in the loop above

  return response;
}
