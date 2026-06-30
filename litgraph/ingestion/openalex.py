"""OpenAlex provider client.

Endpoints (see docs/research/ingestion_api_confirmation.md):

- single:  ``GET /works/{id}``
- batch:   ``GET /works?filter=openalex:W1|W2|...`` (OR-filter, chunked)
- search:  ``GET /works?search=...&per_page=...&cursor=*`` (cursor paging)

The API key, when configured, is sent as the ``api_key`` query parameter.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from litgraph.schemas import PaperRecord, Provider

from .base import ProviderClient


class OpenAlexClient(ProviderClient):
    provider = Provider.OPENALEX

    def get_paper(self, provider_paper_id: str) -> PaperRecord:
        url = self._build_url(f"works/{self._short_id(provider_paper_id)}", self._common_params())
        payload = self._request_json("GET", url)
        return self._to_paper_record(payload)

    def get_papers_batch(self, provider_paper_ids: Sequence[str]) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        for chunk in self._chunk(list(provider_paper_ids), self._settings.batch_size):
            id_filter = "openalex:" + "|".join(self._short_id(pid) for pid in chunk)
            params = self._common_params({"filter": id_filter, "per_page": len(chunk)})
            data = self._request_json("GET", self._build_url("works", params))
            records.extend(self._collect(data.get("results", [])))
        return records

    def search_papers(self, query: str, *, max_results: int) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        cursor: str | None = "*"
        pages = 0
        while cursor and len(records) < max_results and pages < self._settings.max_pages:
            params = self._common_params(
                {"search": query, "per_page": self._settings.page_size, "cursor": cursor}
            )
            data = self._request_json("GET", self._build_url("works", params))
            results = data.get("results", [])
            if not results:
                break
            records.extend(self._collect(results, max_results - len(records)))
            cursor = data.get("meta", {}).get("next_cursor")
            pages += 1
        return records

    # -- helpers ---------------------------------------------------------

    def _record_id(self, payload: Mapping[str, Any]) -> str | None:
        record_id = payload.get("id")
        return str(record_id) if record_id is not None else None

    def _common_params(
        self, extra: Mapping[str, str | int | None] | None = None
    ) -> dict[str, str | int | None]:
        params: dict[str, str | int | None] = {"api_key": self._settings.api_key}
        if extra:
            params.update(extra)
        return params

    @staticmethod
    def _short_id(provider_paper_id: str) -> str:
        """Reduce a full OpenAlex URL id to its bare ``W...`` form for filters."""
        return provider_paper_id.rstrip("/").rsplit("/", 1)[-1]
