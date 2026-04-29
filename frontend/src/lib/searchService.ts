// Search service — single seam between UI and backend.
// Today: returns deterministic mock data. Tomorrow: swap implementation
// for fetch("/search") against the FastAPI backend described in AGENTS.md.

import { MOCK_GAMES } from "./mockData";
import type {
  AlgorithmResult,
  ModelId,
  MultiAlgorithmSearchResponse,
  RankedResult,
  SearchRequest,
} from "./types";

const tokenize = (s: string) =>
  s
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean);

// Hash a string to a stable [0,1) value, used to seed deterministic per-model variation.
const hash = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 10_000) / 10_000;
};

interface ModelKnobs {
  /** Bias toward exact lexical overlap (0..1). */
  lexical: number;
  /** Bias toward semantic / theme overlap (0..1). */
  semantic: number;
  /** Score scale (peak score). */
  scale: number;
  /** Latency baseline in ms. */
  latencyMs: number;
}

const KNOBS: Record<ModelId, ModelKnobs> = {
  bm25:                       { lexical: 1.00, semantic: 0.10, scale: 9.5,  latencyMs: 95  },
  bm25_weighted:              { lexical: 1.00, semantic: 0.20, scale: 12.0, latencyMs: 110 },
  bm25_weighted_embeddings:   { lexical: 0.70, semantic: 0.80, scale: 92,   latencyMs: 195 },
  bert:                       { lexical: 0.40, semantic: 1.00, scale: 0.94, latencyMs: 410 },
  bert_finetuned:             { lexical: 0.45, semantic: 1.10, scale: 0.97, latencyMs: 460 },
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

  // Lexical: exact token overlap with field-name boosts.
  let lex = 0;
  const nameTokens = new Set(tokenize(game.name));
  for (const t of qTokens) {
    if (nameTokens.has(t)) lex += 2.2;
    else if (dSet.has(t)) lex += 1.0;
  }
  lex = lex / Math.max(qTokens.length, 1);

  // Semantic-ish: stem prefix + theme/genre similarity heuristic.
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
  // Mild quality prior so well-rated games surface in semantic models.
  sem += game.rating / 200;

  const noise = (hash(modelSalt + game.id) - 0.5) * 0.3;
  const raw = knobs.lexical * lex + knobs.semantic * sem + noise;
  return Math.max(0, raw) * knobs.scale;
};

export async function executeSearch(
  req: SearchRequest,
): Promise<MultiAlgorithmSearchResponse> {
  // Simulate network/compute latency.
  await new Promise((r) => setTimeout(r, 280));

  const size = req.size ?? 6;
  const response: MultiAlgorithmSearchResponse = {};

  for (const modelId of req.models) {
    const knobs = KNOBS[modelId];
    const scored = MOCK_GAMES.map((g) => ({
      g,
      s: scoreGame(req.query_text, g, knobs, modelId),
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

    const algo: AlgorithmResult = {
      results,
      total: scored.length,
      execution_time_ms:
        knobs.latencyMs + Math.round((hash(modelId + req.query_text) - 0.5) * 30),
    };
    response[modelId] = algo;
  }

  return response;
}
