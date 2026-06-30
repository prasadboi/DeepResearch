"""Common provider-client interface and shared fetch machinery.

`ProviderClient` defines the agent-facing surface (single, batch, and bounded
paged search) and centralizes JSON parsing, bounded retry/rate-limit handling,
and raw-record assembly. Subclasses implement provider-specific URL building,
record-id extraction, and pagination.
"""

from __future__ import annotations

import json
import time
import urllib.parse
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from litgraph.config import ProviderSettings
from litgraph.ingestion.checksums import sha256_canonical_json
from litgraph.ingestion.errors import (
    ProviderError,
    ProviderResponseError,
    ProviderTimeoutError,
    error_for_status,
)
from litgraph.ingestion.transport import (
    Response,
    Transport,
    TransportError,
    UrllibTransport,
    redact,
)
from litgraph.schemas import PaperRecord, Provider

#: Cap on Retry-After / computed backoff sleeps, in seconds.
_MAX_BACKOFF_SECONDS = 60.0


@dataclass(frozen=True)
class FetchContext:
    """Run-scoped identifiers stamped onto every fetched record.

    These come from the caller (an ingestion run), not the provider. The client
    never invents a ``canonical_paper_id``; identity remains the registry's job.
    """

    snapshot_id: str
    fetch_run_id: str


class ProviderClient(ABC):
    """Fetches raw provider records plus fetch metadata behind one interface."""

    #: Provider identity; set by each concrete subclass.
    provider: Provider

    def __init__(
        self,
        settings: ProviderSettings,
        fetch_context: FetchContext,
        *,
        transport: Transport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._ctx = fetch_context
        self._transport = transport or UrllibTransport(settings.timeout_seconds)
        self._sleep = sleep

    # -- public interface ------------------------------------------------

    @abstractmethod
    def get_paper(self, provider_paper_id: str) -> PaperRecord:
        """Fetch a single raw record by the provider's own id."""

    @abstractmethod
    def get_papers_batch(
        self, provider_paper_ids: Sequence[str]
    ) -> list[PaperRecord]:
        """Fetch many raw records, chunked to the provider's batch cap."""

    @abstractmethod
    def search_papers(self, query: str, *, max_results: int) -> list[PaperRecord]:
        """Bounded paged search returning at most ``max_results`` raw records."""

    # -- helpers for subclasses ------------------------------------------

    def _default_headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "User-Agent": "litgraph/0.0.0"}

    def _build_url(
        self, path: str, params: Mapping[str, str | int | None] | None = None
    ) -> str:
        base = self._settings.base_url.rstrip("/")
        url = f"{base}/{path.lstrip('/')}"
        query = {k: v for k, v in (params or {}).items() if v is not None}
        if query:
            # Keep ':' and '|' literal so OpenAlex filter syntax survives.
            url += "?" + urllib.parse.urlencode(query, safe=":|/", quote_via=urllib.parse.quote)
        return url

    def _to_paper_record(self, payload: dict[str, Any]) -> PaperRecord:
        return PaperRecord(
            snapshot_id=self._ctx.snapshot_id,
            provider=self.provider,
            provider_record_id=self._record_id(payload),
            fetch_run_id=self._ctx.fetch_run_id,
            fetched_at=datetime.now(UTC),
            raw_payload=payload,
            raw_checksum=sha256_canonical_json(payload),
        )

    @abstractmethod
    def _record_id(self, payload: Mapping[str, Any]) -> str | None:
        """Extract the provider's own record id from a raw payload."""

    @staticmethod
    def _chunk(ids: Sequence[str], size: int) -> Iterator[Sequence[str]]:
        for start in range(0, len(ids), size):
            yield ids[start : start + size]

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> Any:
        merged = self._default_headers()
        if headers:
            merged.update(headers)

        attempt = 0
        while True:
            try:
                resp = self._transport.fetch(method, url, headers=merged, body=body)
            except TransportError as exc:
                raise ProviderTimeoutError(self.provider, str(exc)) from exc

            if 200 <= resp.status < 300:
                return self._parse_json(resp)

            if (resp.status == 429 or 500 <= resp.status < 600) and (
                attempt < self._settings.max_retries
            ):
                self._sleep(self._retry_delay(attempt, resp))
                attempt += 1
                continue

            raise error_for_status(
                self.provider, resp.status, self._error_message(resp, url)
            )

    def _parse_json(self, resp: Response) -> Any:
        try:
            return json.loads(resp.body)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProviderResponseError(
                self.provider, f"unparseable response body: {exc}", status_code=resp.status
            ) from exc

    def _retry_delay(self, attempt: int, resp: Response) -> float:
        retry_after = resp.headers.get("retry-after")
        if retry_after is not None:
            try:
                return min(float(retry_after), _MAX_BACKOFF_SECONDS)
            except ValueError:
                pass
        return min(
            self._settings.backoff_base_seconds * (2**attempt), _MAX_BACKOFF_SECONDS
        )

    def _error_message(self, resp: Response, url: str) -> str:
        snippet = resp.body[:200].decode("utf-8", errors="replace")
        return f"HTTP {resp.status} for {redact(url)}: {snippet}"

    def _collect(
        self, payloads: Iterable[Mapping[str, Any]], limit: int | None = None
    ) -> list[PaperRecord]:
        records: list[PaperRecord] = []
        for payload in payloads:
            if limit is not None and len(records) >= limit:
                break
            records.append(self._to_paper_record(dict(payload)))
        return records


__all__ = ["FetchContext", "ProviderClient", "ProviderError"]
