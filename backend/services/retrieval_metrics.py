"""
IR metrics via ranx (graded qrels + run scores from ranking).
"""

from __future__ import annotations

from ranx import Qrels, Run, evaluate

from models.search import RankedResult, RetrievalMetrics


def _ranx_metric_names(size: int) -> list[str]:
    names = ["precision@1", "ndcg@1", "recall@1", "f1@1", "map"]
    if size >= 5:
        names.extend(["precision@5", "ndcg@5", "recall@5", "f1@5"])
    if size >= 10:
        names.extend(["precision@10", "ndcg@10", "recall@10", "f1@10"])
    return names


def _metrics_from_ranx(raw: dict[str, float], size: int) -> RetrievalMetrics:
    def pick(name: str) -> float:
        return float(raw[name])

    data: dict[str, float] = {
        "precision_at_1": pick("precision@1"),
        "ndcg_at_1": pick("ndcg@1"),
        "f1_at_1": pick("f1@1"),
        "mean_average_precision": pick("map"),
    }
    if size >= 5:
        data["precision_at_5"] = pick("precision@5")
        data["ndcg_at_5"] = pick("ndcg@5")
        data["f1_at_5"] = pick("f1@5")
    if size >= 10:
        data["precision_at_10"] = pick("precision@10")
        data["ndcg_at_10"] = pick("ndcg@10")
        data["f1_at_10"] = pick("f1@10")
    return RetrievalMetrics(**data)


def _zero_metrics(size: int) -> RetrievalMetrics:
    data: dict[str, float] = {
        "precision_at_1": 0.0,
        "ndcg_at_1": 0.0,
        "f1_at_1": 0.0,
        "mean_average_precision": 0.0,
    }
    if size >= 5:
        data.update(
            {
                "precision_at_5": 0.0,
                "ndcg_at_5": 0.0,
                "f1_at_5": 0.0,
            }
        )
    if size >= 10:
        data.update(
            {
                "precision_at_10": 0.0,
                "ndcg_at_10": 0.0,
                "f1_at_10": 0.0,
            }
        )
    return RetrievalMetrics(**data)


def compute_retrieval_metrics(
    query_key: str,
    ranked_results: list[RankedResult],
    graded_qrels: dict[str, float],
    size: int,
) -> RetrievalMetrics:
    """
    Evaluate one ranked list for a single query using ranx.

    ``size`` is the requested result count; @5 metrics require ``size >= 5``,
    @10 metrics require ``size >= 10``.
    """
    if not graded_qrels:
        return _zero_metrics(size)

    qrels_obj = Qrels({query_key: dict(graded_qrels)})

    if not ranked_results:
        return _zero_metrics(size)

    run_obj = Run({query_key: {str(r.id): float(r.score) for r in ranked_results}})
    raw = evaluate(qrels_obj, run_obj, _ranx_metric_names(size))
    return _metrics_from_ranx(raw, size)
