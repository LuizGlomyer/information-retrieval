"""Generate graded qrels for top-k BM25 candidates using Gemini."""

from __future__ import annotations

import json
from typing import Any

from elasticsearch import Elasticsearch
from google import genai
from google.genai import types

from config import config
from models.search import Bm25IdNameSearchRequest, GenerateQrelsRequest, GenerateQrelsResponse
from services.qrels import QREL_SUPER_MARIO, QREL_MORTAL_KOMBAT, QREL_SPARTAN_WARRIOR_PROTAGONIST, QREL_BASKETBALL_GOOD_MOVEMENT


QUERY_QRELS = {
    "super mario": QREL_SUPER_MARIO,
    "combat that is mortal": QREL_MORTAL_KOMBAT, 
    "spartan warrior protagonist": QREL_SPARTAN_WARRIOR_PROTAGONIST,
    "basketball with good movement": QREL_BASKETBALL_GOOD_MOVEMENT,
}


def normalized_query_key(query_text: str) -> str:
    """Single normalization rule for qrels lookup and validation."""
    return query_text.strip()


def graded_qrels_for_query(query_text: str) -> dict[str, float]:
    """
    Return doc_id -> relevance grade for the normalized query key.

    Returns an empty dict when the query is not in ``QUERY_QRELS`` or has no grades.
    """
    key = normalized_query_key(query_text)
    raw = QUERY_QRELS.get(key)
    if not raw:
        return {}
    return {
        str(doc_id): float(grade)
        for doc_id, grade in raw.items()
        if isinstance(grade, (int, float)) and not isinstance(grade, bool)
    }


class QrelsGenerationError(Exception):
    """Base error for qrels generation."""


class MissingGeminiApiKeyError(QrelsGenerationError):
    """Raised when GEMINI_API_KEY is not configured."""


class GeminiApiError(QrelsGenerationError):
    """Raised when the Gemini API call fails."""


class InvalidLlmResponseError(QrelsGenerationError):
    """Raised when Gemini returns unparseable or invalid qrels JSON."""


class QrelsGenerationService:
    @staticmethod
    def generate(
        es_client: Elasticsearch, request: GenerateQrelsRequest
    ) -> GenerateQrelsResponse:
        if not config.GEMINI_API_KEY:
            raise MissingGeminiApiKeyError("GEMINI_API_KEY is not configured")

        from services.search import SearchService

        query_key = normalized_query_key(request.query_text)
        base_search_request = Bm25IdNameSearchRequest(
            query_text=request.query_text,
            size=request.size,
            filters=request.filters,
            name_only=True,
            hybrid=False,
        )

        bm25_results = SearchService.execute_bm25_id_name_search(
            es_client=es_client, request=base_search_request
        )

        hybrid_search_request = base_search_request.model_copy(update={"hybrid": True})
        bm25_hybrid_results = SearchService.execute_bm25_id_name_search(
            es_client=es_client, request=hybrid_search_request
        )

        search_request = base_search_request.model_copy(update={"name_only": True, "hybrid": False})
        bert_results = SearchService.execute_bert_id_name_search(
            es_client=es_client, request=search_request
        )
        svm_results = SearchService.execute_svm_id_name_search(
            es_client=es_client, request=search_request
        )

        all_results = []
        seen_ids = set()

        for result_set in (bm25_results, bm25_hybrid_results, bert_results, svm_results):
            for result in result_set.results:
                if result.id not in seen_ids:
                    seen_ids.add(result.id)
                    all_results.append({"id": result.id, "name": result.name})

        print(f"Qrels generation will judge {len(all_results)} unique candidates for query={request.query_text!r}")

        if not all_results:
            return GenerateQrelsResponse(
                filtered={"total": 0, "qrels": {}},
                gemini_response={"total": 0, "qrels": {}},
            )

        raw_grades = QrelsGenerationService._grade_with_gemini(
            query_text=request.query_text,
            candidates=all_results,
        )
        validated = QrelsGenerationService._validate_grades(raw_grades, seen_ids)
        print(f"Gemini returned grades for {len(validated)} documents")
        filtered = {
            doc_id: grade for doc_id, grade in validated.items() if grade > 0
        }
        print(f"Filtered to {len(filtered)} relevant documents (grade > 0)")
        
        return GenerateQrelsResponse(
            filtered={"total": len(filtered), "qrels": {query_key: filtered}},
            gemini_response={"total": len(raw_grades), "qrels": {query_key: raw_grades}},
        )

    @staticmethod
    def _grade_with_gemini(
        query_text: str, candidates: list[dict[str, str]]
    ) -> dict[str, Any]:
        candidates_json = json.dumps(candidates, ensure_ascii=True)
        prompt = (
            "You are judging search relevance for a video game catalog.\n\n"
            f"Query: {query_text!r}\n\n"
            f"Candidate games (JSON array): {candidates_json}\n\n"
            "For each candidate game id, assign an integer relevance grade:\n"
            "- 0: not relevant\n"
            "- 1: marginally relevant\n"
            "- 2: relevant\n"
            "- 3: highly relevant (exact or very strong match)\n\n"
            "Return a single JSON object mapping each game id (as a string key) "
            "to its grade (integer 0-3). Include every candidate id."
        )

        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:
            raise GeminiApiError(f"Gemini API call failed: {exc}") from exc

        text = response.text
        if not text:
            raise InvalidLlmResponseError("Gemini returned empty response")

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidLlmResponseError(
                f"Invalid JSON from Gemini: {exc}"
            ) from exc

        if not isinstance(parsed, dict):
            raise InvalidLlmResponseError("Gemini response must be a JSON object")

        return parsed

    @staticmethod
    def _validate_grades(
        raw: dict[Any, Any], candidate_ids: set[str]
    ) -> dict[str, int]:
        validated: dict[str, int] = {}
        for doc_id, grade in raw.items():
            doc_id_str = str(doc_id)
            if doc_id_str not in candidate_ids:
                continue
            if isinstance(grade, bool) or not isinstance(grade, (int, float)):
                raise InvalidLlmResponseError(
                    f"Invalid grade for {doc_id_str}: {grade!r}"
                )
            grade_int = int(grade)
            if grade_int < 0 or grade_int > 3:
                raise InvalidLlmResponseError(
                    f"Grade out of range for {doc_id_str}: {grade_int}"
                )
            validated[doc_id_str] = grade_int
        return validated
