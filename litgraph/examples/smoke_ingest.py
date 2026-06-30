"""Tiny smoke ingestion (Stage 1, Task 1.1).

Exercises both provider clients through the common interface (single, batch, and
bounded paged search), prints provider name + fetch timestamp + record counts,
and asserts that no ``canonical_paper_id`` is created. **Offline by default**
(replays small in-module payloads through a fake transport — no network, no
persistence). The optional ``--live`` flag performs one real fetch per provider
using configured settings; it is skipped by default and is the only path that
touches the network.

Run with::

    python -m litgraph.examples.smoke_ingest          # offline, deterministic
    python -m litgraph.examples.smoke_ingest --live    # real API calls (opt-in)
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from typing import Any

from litgraph.config import load_config
from litgraph.ingestion.base import FetchContext, ProviderClient
from litgraph.ingestion.errors import ProviderError
from litgraph.ingestion.openalex import OpenAlexClient
from litgraph.ingestion.semantic_scholar import SemanticScholarClient
from litgraph.ingestion.transport import Response, Transport
from litgraph.schemas import PaperRecord

_CTX = FetchContext(snapshot_id="smoke-snapshot", fetch_run_id="smoke-run")

# Small in-module sample payloads (shape only; not real provider dumps).
_OA1: dict[str, Any] = {"id": "https://openalex.org/W1", "title": "A", "publication_year": 2020}
_OA2: dict[str, Any] = {"id": "https://openalex.org/W2", "title": "B", "publication_year": 2021}
_S2A: dict[str, Any] = {"paperId": "p1", "title": "A", "year": 2020}
_S2B: dict[str, Any] = {"paperId": "p2", "title": "B", "year": 2021}


class _ReplayTransport:
    """Returns queued canned responses; used for the offline smoke."""

    def __init__(self, responses: Sequence[Response]) -> None:
        self._responses = list(responses)

    def fetch(
        self, method: str, url: str, *, headers: Mapping[str, str], body: bytes | None = None
    ) -> Response:
        return self._responses.pop(0)


def _r(status: int, payload: object) -> Response:
    return Response(status=status, body=json.dumps(payload).encode("utf-8"), headers={})


def _oa(transport: Transport) -> OpenAlexClient:
    return OpenAlexClient(
        load_config().providers.openalex, _CTX, transport=transport, sleep=lambda _: None
    )


def _s2(transport: Transport) -> SemanticScholarClient:
    return SemanticScholarClient(
        load_config().providers.semantic_scholar, _CTX, transport=transport, sleep=lambda _: None
    )


def run_offline() -> dict[str, list[PaperRecord]]:
    """Fetch raw records from both providers via replayed responses."""
    openalex: list[PaperRecord] = []
    openalex.append(_oa(_ReplayTransport([_r(200, _OA1)])).get_paper(_OA1["id"]))
    openalex.extend(
        _oa(_ReplayTransport([_r(200, {"results": [_OA1, _OA2]})])).get_papers_batch(["W1", "W2"])
    )
    openalex.extend(
        _oa(
            _ReplayTransport([_r(200, {"meta": {"next_cursor": None}, "results": [_OA1, _OA2]})])
        ).search_papers("graphs", max_results=2)
    )

    semantic: list[PaperRecord] = []
    semantic.append(_s2(_ReplayTransport([_r(200, _S2A)])).get_paper("p1"))
    semantic.extend(
        _s2(_ReplayTransport([_r(200, [_S2A, _S2B])])).get_papers_batch(["p1", "p2"])
    )
    semantic.extend(
        _s2(
            _ReplayTransport([_r(200, {"data": [_S2A, _S2B], "token": None})])
        ).search_papers("rate limiting", max_results=2)
    )
    return {"openalex": openalex, "semantic_scholar": semantic}


def run_live() -> dict[str, list[PaperRecord]]:
    """Fetch one real record per provider (opt-in; network access)."""
    config = load_config()
    clients: dict[str, tuple[ProviderClient, str]] = {
        "openalex": (
            OpenAlexClient(config.providers.openalex, _CTX),
            "W2741809807",
        ),
        "semantic_scholar": (
            SemanticScholarClient(config.providers.semantic_scholar, _CTX),
            "DOI:10.18653/v1/N18-3011",
        ),
    }
    out: dict[str, list[PaperRecord]] = {}
    for name, (client, paper_id) in clients.items():
        out[name] = [client.get_paper(paper_id)]
    return out


def _assert_no_canonical_ids(records: list[PaperRecord]) -> None:
    for record in records:
        assert not hasattr(record, "canonical_paper_id")
        assert "canonical_paper_id" not in record.raw_payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LitGraph smoke ingestion")
    parser.add_argument(
        "--live", action="store_true", help="perform real API calls (off by default)"
    )
    args = parser.parse_args(argv)

    try:
        results = run_live() if args.live else run_offline()
    except ProviderError as exc:
        print(f"[smoke_ingest] provider error: {exc}")
        return 1

    mode = "live" if args.live else "offline"
    print(f"[smoke_ingest] mode={mode}")
    for provider, records in results.items():
        _assert_no_canonical_ids(records)
        sample = records[0]
        print(
            f"[smoke_ingest] {provider}: records={len(records)} "
            f"fetched_at={sample.fetched_at.isoformat()} "
            f"first_id={sample.provider_record_id}"
        )
    print("[smoke_ingest] OK: raw records fetched, provider+timestamp recorded, no canonical IDs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
