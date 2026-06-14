"""Generate graded qrels for top-k BM25 candidates using Gemini."""

from __future__ import annotations

import json
from typing import Any

from elasticsearch import Elasticsearch
from google import genai
from google.genai import types

from config import config
from models.search import Bm25IdNameSearchRequest, GenerateQrelsRequest
from qrels import normalized_query_key
from services.search import SearchService


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
    ) -> dict[str, dict[str, int]]:
        if not config.GEMINI_API_KEY:
            raise MissingGeminiApiKeyError("GEMINI_API_KEY is not configured")

        query_key = normalized_query_key(request.query_text)
        bm25_request = Bm25IdNameSearchRequest(
            query_text=request.query_text,
            size=request.size,
            filters=request.filters,
            name_only=True,
            hybrid=False,
        )
        search_response = SearchService.execute_bm25_id_name_search(
            es_client=es_client, request=bm25_request
        )
        if not search_response.results:
            return {query_key: {}}

        candidates = [
            {"id": result.id, "name": result.name}
            for result in search_response.results
        ]
        candidate_ids = {result.id for result in search_response.results}
        raw_grades = QrelsGenerationService._grade_with_gemini(
            query_text=request.query_text,
            candidates=candidates,
        )
        validated = QrelsGenerationService._validate_grades(raw_grades, candidate_ids)
        filtered = {
            doc_id: grade for doc_id, grade in validated.items() if grade > 0
        }
        return {query_key: filtered}

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
