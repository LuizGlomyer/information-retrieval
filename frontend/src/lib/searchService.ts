import type {
  ModelId,
  MultiAlgorithmSearchResponse,
  RankedResult,
  SearchRequest,
} from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

// Backend API result interfaces
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
  metrics?: any;
}

async function fetchFromBackend(
  queryText: string,
  size: number,
  rerank: boolean,
  metrics: boolean,
): Promise<Record<string, BackendAlgorithmResult> | null> {
  try {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query_text: queryText,
        size,
        rerank,
        metrics,
      }),
      signal: AbortSignal.timeout(15_000),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData?.detail || `API error (${res.status})`);
    }
    return await res.json();
  } catch (error: any) {
    if (error.name === "TimeoutError") {
      throw new Error("A requisição ao servidor excedeu o tempo limite.");
    }
    throw error;
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

export async function executeSearch(
  req: SearchRequest,
): Promise<MultiAlgorithmSearchResponse> {
  const size = req.size ?? 6;
  const rerank = req.rerank ?? false;
  const metrics = req.metrics ?? false;

  // Fetch results from the backend router
  const backendData = await fetchFromBackend(req.query_text, size, rerank, metrics);

  if (!backendData) {
    throw new Error("Não foi possível conectar ao servidor de busca. Certifique-se de que o backend está ativo.");
  }

  const response: MultiAlgorithmSearchResponse = {};

  for (const modelId of req.models) {
    // Determine the key in the backend response dictionary:
    // if rerank is active, we map base model to its *_crossencoder sibling.
    const targetKey = (rerank ? `${modelId}_crossencoder` : modelId) as ModelId;
    const algo = backendData[targetKey];

    if (algo) {
      response[modelId] = {
        results: algo.results.map((r) => mapBackendResult(r, targetKey)),
        total: algo.total,
        execution_time_ms: algo.execution_time_ms,
        metrics: algo.metrics,
      };
    } else {
      throw new Error(`Modelo de busca '${modelId}' indisponível no backend.`);
    }
  }

  return response;
}
