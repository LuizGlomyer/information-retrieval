"""
IR metrics via ranx (graded qrels + run scores from ranking).
"""

from __future__ import annotations

from ranx import Qrels, Run, evaluate

from models.search import RankedResult, RetrievalMetrics

RANX_METRICS = [
    "precision@1",
    "precision@5",
    "precision@10",
    "map",
    "f1@10",
    "ndcg@1",
    "ndcg@5",
    "ndcg@10",
]


def _zero_metrics() -> RetrievalMetrics:
    return RetrievalMetrics(
        precision_at_1=0.0,
        precision_at_5=0.0,
        precision_at_10=0.0,
        mean_average_precision=0.0,
        f1=0.0,
        ndcg_at_1=0.0,
        ndcg_at_5=0.0,
        ndcg_at_10=0.0,
    )


def compute_retrieval_metrics(
    query_key: str,
    ranked_results: list[RankedResult],
    graded_qrels: dict[str, float],
) -> RetrievalMetrics:
    """
    Evaluate one ranked list for a single query using ranx.

    ``graded_qrels`` maps document id to relevance grade (non-empty).
    ``ranked_results`` provides doc ids and scores for ``ranx.Run`` (higher score = more relevant).
    """
    if not graded_qrels:
        return _zero_metrics()

    qrels_obj = Qrels({query_key: dict(graded_qrels)})

    if not ranked_results:
        return _zero_metrics()

    run_obj = Run({query_key: {str(r.id): float(r.score) for r in ranked_results}})
    raw = evaluate(qrels_obj, run_obj, RANX_METRICS)

    def pick(name: str) -> float:
        return float(raw[name])

    return RetrievalMetrics(
        precision_at_1=pick("precision@1"),
        precision_at_5=pick("precision@5"),
        precision_at_10=pick("precision@10"),
        mean_average_precision=pick("map"),
        f1=pick("f1@10"),
        ndcg_at_1=pick("ndcg@1"),
        ndcg_at_5=pick("ndcg@5"),
        ndcg_at_10=pick("ndcg@10"),
    )
