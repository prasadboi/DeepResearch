"""Construction tests for the provider ingestion clients (offline, fixture-backed)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from litgraph.config import ProviderSettings
from litgraph.ingestion.base import FetchContext
from litgraph.ingestion.errors import (
    ProviderBadRequestError,
    ProviderError,
    ProviderNotFoundError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from litgraph.ingestion.openalex import OpenAlexClient
from litgraph.ingestion.semantic_scholar import SemanticScholarClient
from litgraph.ingestion.transport import Response, TransportError
from litgraph.schemas import PaperRecord, Provider

CTX = FetchContext(snapshot_id="snap-1", fetch_run_id="run-1")


def _noop_sleep(_: float) -> None:
    return None


def _resp(status: int, payload: object) -> Response:
    return Response(status=status, body=json.dumps(payload).encode("utf-8"), headers={})


class FakeTransport:
    """Returns a queue of canned responses (or raises queued exceptions)."""

    def __init__(self, items: Sequence[Response | Exception]) -> None:
        self._items = list(items)
        self.calls: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def fetch(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> Response:
        self.calls.append((method, url, dict(headers), body))
        item = self._items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _load(fixtures_dir: Path, name: str) -> dict:
    return json.loads((fixtures_dir / name).read_text(encoding="utf-8"))


def _openalex(settings: ProviderSettings, transport: FakeTransport) -> OpenAlexClient:
    return OpenAlexClient(settings, CTX, transport=transport, sleep=_noop_sleep)


def _s2(settings: ProviderSettings, transport: FakeTransport) -> SemanticScholarClient:
    return SemanticScholarClient(settings, CTX, transport=transport, sleep=_noop_sleep)


def _oa_settings(**kw: object) -> ProviderSettings:
    return ProviderSettings(base_url="https://api.openalex.org", **kw)  # type: ignore[arg-type]


def _s2_settings(**kw: object) -> ProviderSettings:
    return ProviderSettings(base_url="https://api.semanticscholar.org/graph/v1", **kw)  # type: ignore[arg-type]


# -- required construction tests -----------------------------------------


def test_openalex_client_parses_mock_response(fixtures_dir: Path) -> None:
    work = _load(fixtures_dir, "openalex_work.json")
    transport = FakeTransport([_resp(200, work)])
    record = _openalex(_oa_settings(), transport).get_paper(work["id"])

    assert record.provider is Provider.OPENALEX
    assert record.raw_payload == work
    assert record.provider_record_id == work["id"]
    assert record.fetched_at is not None
    assert len(record.raw_checksum) == 64
    assert record.snapshot_id == "snap-1"
    assert record.fetch_run_id == "run-1"
    # single lookup hits /works/{bare-id}
    assert transport.calls[0][1].endswith("/works/W2741809807")


def test_semantic_scholar_client_parses_mock_response(fixtures_dir: Path) -> None:
    paper = _load(fixtures_dir, "semantic_scholar_paper.json")
    transport = FakeTransport([_resp(200, paper)])
    record = _s2(_s2_settings(), transport).get_paper("DOI:10.18653/v1/N18-3011")

    assert record.provider is Provider.SEMANTIC_SCHOLAR
    assert record.raw_payload == paper
    assert record.provider_record_id == paper["paperId"]
    assert len(record.raw_checksum) == 64
    # rich fields must be requested explicitly
    assert "fields=" in transport.calls[0][1]
    # no key configured -> no auth header leaked
    assert "x-api-key" not in transport.calls[0][2]


def test_provider_error_is_typed(fixtures_dir: Path) -> None:
    not_found = _openalex(_oa_settings(), FakeTransport([_resp(404, {"error": "not found"})]))
    with pytest.raises(ProviderNotFoundError) as nf:
        not_found.get_paper("W404")
    assert isinstance(nf.value, ProviderError)
    assert nf.value.status_code == 404

    server = _openalex(_oa_settings(max_retries=0), FakeTransport([_resp(500, {"error": "boom"})]))
    with pytest.raises(ProviderResponseError):
        server.get_paper("W500")

    # persistent 429 retries exactly max_retries+1 times, then raises.
    rl_transport = FakeTransport([_resp(429, {}), _resp(429, {}), _resp(429, {})])
    rate_limited = _openalex(_oa_settings(max_retries=2), rl_transport)
    with pytest.raises(ProviderRateLimitError):
        rate_limited.get_paper("W429")
    assert len(rl_transport.calls) == 3

    timed_out = _openalex(_oa_settings(), FakeTransport([TransportError("conn reset")]))
    with pytest.raises(ProviderError):
        timed_out.get_paper("Wxxx")


def test_provider_client_does_not_create_canonical_ids(fixtures_dir: Path) -> None:
    work = _load(fixtures_dir, "openalex_work.json")
    record = _openalex(_oa_settings(), FakeTransport([_resp(200, work)])).get_paper(work["id"])

    assert "canonical_paper_id" not in PaperRecord.model_fields
    assert not hasattr(record, "canonical_paper_id")
    # provider's own id is preserved; nothing minted, payload untouched.
    assert record.provider_record_id.startswith("https://openalex.org/W")
    assert record.raw_payload == work
    assert "canonical_paper_id" not in record.raw_payload


# -- extra coverage ------------------------------------------------------


def test_get_papers_batch_chunks_and_parses(fixtures_dir: Path) -> None:
    # OpenAlex OR-filter batching, chunked to 2.
    oa_transport = FakeTransport(
        [
            _resp(200, {"results": [{"id": "https://openalex.org/W1"}, {"id": "https://openalex.org/W2"}]}),
            _resp(200, {"results": [{"id": "https://openalex.org/W3"}]}),
        ]
    )
    oa = _openalex(_oa_settings(batch_size=2), oa_transport)
    oa_records = oa.get_papers_batch(["W1", "W2", "W3"])
    assert len(oa_records) == 3
    assert len(oa_transport.calls) == 2
    assert "filter=openalex:W1|W2" in oa_transport.calls[0][1]

    # S2 POST /paper/batch, chunked to 2; null entries are skipped.
    s2_transport = FakeTransport(
        [
            _resp(200, [{"paperId": "p1"}, {"paperId": "p2"}]),
            _resp(200, [{"paperId": "p3"}, None]),
        ]
    )
    s2 = _s2(_s2_settings(batch_size=2), s2_transport)
    s2_records = s2.get_papers_batch(["p1", "p2", "p3", "p4"])
    assert [r.provider_record_id for r in s2_records] == ["p1", "p2", "p3"]
    assert len(s2_transport.calls) == 2
    assert all(call[0] == "POST" for call in s2_transport.calls)


def test_search_papers_follows_pagination(fixtures_dir: Path) -> None:
    # OpenAlex cursor paging across two pages.
    page1 = _load(fixtures_dir, "openalex_search.json")
    oa_transport = FakeTransport(
        [_resp(200, page1), _resp(200, {"meta": {"next_cursor": None}, "results": []})]
    )
    oa_records = _openalex(_oa_settings(page_size=2), oa_transport).search_papers(
        "open access", max_results=10
    )
    assert len(oa_records) == 2
    assert len(oa_transport.calls) == 2
    assert page1["meta"]["next_cursor"] in oa_transport.calls[1][1]

    # max_results caps the result set and stops paging early.
    capped_transport = FakeTransport([_resp(200, page1)])
    capped = _openalex(_oa_settings(page_size=2), capped_transport).search_papers(
        "open access", max_results=1
    )
    assert len(capped) == 1
    assert len(capped_transport.calls) == 1

    # S2 bulk token paging across two pages.
    s2_page1 = _load(fixtures_dir, "semantic_scholar_search.json")
    s2_transport = FakeTransport([_resp(200, s2_page1), _resp(200, {"data": [], "token": None})])
    s2_records = _s2(_s2_settings(), s2_transport).search_papers("rate limiting", max_results=10)
    assert len(s2_records) == 2
    assert "token=" in s2_transport.calls[1][1]


def test_request_url_redacts_api_key() -> None:
    from litgraph.ingestion.transport import redact

    redacted = redact("https://api.openalex.org/works?api_key=SUPERSECRET&search=x")
    assert "SUPERSECRET" not in redacted
    assert "api_key=REDACTED" in redacted

    transport = FakeTransport([_resp(400, {"error": "bad request"})])
    client = _openalex(_oa_settings(api_key="SUPERSECRET"), transport)
    with pytest.raises(ProviderBadRequestError) as err:
        client.get_paper("W1")
    assert "SUPERSECRET" not in str(err.value)
    assert "REDACTED" in str(err.value)
