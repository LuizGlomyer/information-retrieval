"""
Query relevance judgments (qrels) with graded relevance.

Keys are query strings (match what clients send in ``query_text`` after trimming).
Values map **document id** (use strings, e.g. ``\"2191\"``) to a **numeric relevance grade**
(``int`` or ``float``). These grades are passed to ``ranx.Qrels`` for NDCG / MAP / etc.

Example::

    QUERY_QRELS = {
        "super mario": {"2191": 3, "734": 2, "105": 1},
    }
"""

from __future__ import annotations

from typing import Dict, Union

# Document ids should be strings (e.g. "2191") for consistency with API ``id`` fields.
QUERY_QRELS: Dict[str, Dict[str, Union[int, float]]] = {
    "super mario": {"21919": 3,},
}


def normalized_query_key(query_text: str) -> str:
    """Single normalization rule for qrels lookup and validation."""
    return query_text.strip()


def graded_qrels_for_query(query_text: str) -> dict[str, float]:
    """
    Return doc_id -> relevance grade for the normalized query key.
    Caller must ensure the key exists in ``QUERY_QRELS``.
    """
    key = normalized_query_key(query_text)
    raw = QUERY_QRELS[key]
    return {str(doc_id): float(grade) for doc_id, grade in raw.items()}
