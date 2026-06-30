"""Semantic Scholar (Academic Graph) provider client.

Endpoints (see docs/research/ingestion_api_confirmation.md):

- single:  ``GET /paper/{id}?fields=...``
- batch:   ``POST /paper/batch`` body ``{"ids": [...]}`` (chunked to 500) ``?fields=...``
- search:  ``GET /paper/search/bulk?query=...&fields=...&token=...`` (token paging)

S2 returns only ``paperId``/``title`` unless ``fields`` is given, so the client
requests a fixed superset; that is field *selection*, not payload mutation. The
API key, when configured, is sent as the ``x-api-key`` header.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from litgraph.schemas import PaperRecord, Provider

from .base import ProviderClient

#: Raw fields requested from S2 (a superset; stored verbatim).
FIXED_FIELDS = (
    "title,abstract,year,venue,publicationVenue,authors,externalIds,"
    "citationCount,referenceCount,openAccessPdf,isOpenAccess,fieldsOfStudy,"
    "publicationTypes,publicationDate,url"
)


class SemanticScholarClient(ProviderClient):
    provider = Provider.SEMANTIC_SCHOLAR

    def get_paper(self, provider_paper_id: str) -> PaperRecord:
        url = self._build_url(f"paper/{provider_paper_id}", {"fields": FIXED_FIELDS})
        payload = self._request_json("GET", url)
        return self._to_paper_record(payload)

    def get_papers_batch(self, provider_paper_ids: Sequence[str]) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        url = self._build_url("paper/batch", {"fields": FIXED_FIELDS})
        for chunk in self._chunk(list(provider_paper_ids), self._settings.batch_size):
            body = json.dumps({"ids": list(chunk)}).encode("utf-8")
            data = self._request_json(
                "POST", url, headers={"Content-Type": "application/json"}, body=body
            )
            # The batch endpoint returns a list with `null` for unresolved ids.
            records.extend(self._collect(item for item in data if item is not None))
        return records

    def search_papers(self, query: str, *, max_results: int) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        token: str | None = None
        pages = 0
        while len(records) < max_results and pages < self._settings.max_pages:
            params: dict[str, str | int | None] = {"query": query, "fields": FIXED_FIELDS}
            if token is not None:
                params["token"] = token
            data = self._request_json("GET", self._build_url("paper/search/bulk", params))
            items = data.get("data", [])
            if not items:
                break
            records.extend(self._collect(items, max_results - len(records)))
            token = data.get("token")
            pages += 1
            if token is None:
                break
        return records

    # -- helpers ---------------------------------------------------------

    def _default_headers(self) -> dict[str, str]:
        headers = super()._default_headers()
        if self._settings.api_key:
            headers["x-api-key"] = self._settings.api_key
        return headers

    def _record_id(self, payload: Mapping[str, Any]) -> str | None:
        record_id = payload.get("paperId")
        return str(record_id) if record_id is not None else None
