"""Construction tests for the local raw snapshot store (offline, tmp_path)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from litgraph.ingestion.checksums import sha256_file
from litgraph.ingestion.raw_store import (
    RawSnapshotStore,
    RawStoreError,
    SnapshotExistsError,
)
from litgraph.schemas import PaperRecord, Provider

SNAP = "snap-test"


def _record(provider: Provider, record_id: str, *, snapshot_id: str = SNAP) -> PaperRecord:
    return PaperRecord(
        snapshot_id=snapshot_id,
        provider=provider,
        provider_record_id=record_id,
        fetch_run_id="run-1",
        fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
        raw_payload={"id": record_id, "title": "x"},
        raw_checksum="deadbeef",
    )


def _records() -> dict[Provider, list[PaperRecord]]:
    return {
        Provider.OPENALEX: [_record(Provider.OPENALEX, "W1"), _record(Provider.OPENALEX, "W2")],
        Provider.SEMANTIC_SCHOLAR: [_record(Provider.SEMANTIC_SCHOLAR, "p1")],
    }


def test_raw_store_writes_jsonl(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    snapshot = store.write_snapshot(SNAP, _records())
    snap_dir = store.snapshot_dir(SNAP)

    assert (snap_dir / "openalex.jsonl").exists()
    assert (snap_dir / "semantic_scholar.jsonl").exists()
    assert (snap_dir / "openalex.manifest.json").exists()
    assert (snap_dir / "snapshot.manifest.json").exists()

    lines = [ln for ln in (snap_dir / "openalex.jsonl").read_text().splitlines() if ln.strip()]
    assert len(lines) == 2

    records = list(store.iter_records(SNAP, Provider.OPENALEX))
    assert [r.provider_record_id for r in records] == ["W1", "W2"]
    assert all(r.provider is Provider.OPENALEX for r in records)
    assert snapshot.total_record_count == 3
    assert set(snapshot.providers) == {Provider.OPENALEX, Provider.SEMANTIC_SCHOLAR}


def test_raw_store_refuses_overwrite_without_force(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    store.write_snapshot(SNAP, _records())
    original = (store.snapshot_dir(SNAP) / "openalex.jsonl").read_bytes()

    with pytest.raises(SnapshotExistsError):
        store.write_snapshot(SNAP, _records())
    # append-only: the refused write must not have mutated existing data.
    assert (store.snapshot_dir(SNAP) / "openalex.jsonl").read_bytes() == original

    store.write_snapshot(SNAP, _records(), force=True)
    assert store.validate_snapshot(SNAP).ok


def test_manifest_contains_checksum(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    snapshot = store.write_snapshot(SNAP, _records())
    manifest = store.read_ingestion_manifest(SNAP, Provider.OPENALEX)

    assert manifest.checksum
    assert manifest.checksum == sha256_file(store.snapshot_dir(SNAP) / manifest.file)
    assert snapshot.checksum


def test_manifest_record_count_matches_file(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    store.write_snapshot(SNAP, _records())
    manifest = store.read_ingestion_manifest(SNAP, Provider.OPENALEX)

    path = store.snapshot_dir(SNAP) / manifest.file
    lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
    assert manifest.record_count == len(lines) == 2
    assert store.read_snapshot_manifest(SNAP).total_record_count == 3


def test_validate_snapshot_detects_tampering(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    store.write_snapshot(SNAP, _records())
    assert store.validate_snapshot(SNAP).ok

    path = store.snapshot_dir(SNAP) / "openalex.jsonl"
    path.write_text(path.read_text() + '{"id": "W3"}\n')

    report = store.validate_snapshot(SNAP)
    assert not report.ok
    assert report.issues


def test_stored_records_have_no_canonical_id(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    store.write_snapshot(SNAP, _records())
    text = (store.snapshot_dir(SNAP) / "openalex.jsonl").read_text()
    assert "canonical_paper_id" not in text

    bad = _record(Provider.OPENALEX, "W9", snapshot_id="snap2")
    bad.raw_payload["canonical_paper_id"] = "cp-x"
    with pytest.raises(RawStoreError):
        store.write_snapshot("snap2", {Provider.OPENALEX: [bad]})


def test_source_query_secrets_redacted(tmp_path: Path) -> None:
    store = RawSnapshotStore(tmp_path)
    store.write_snapshot(SNAP, _records(), source_query={"q": "x", "api_key": "SECRET"})
    manifest = store.read_ingestion_manifest(SNAP, Provider.OPENALEX)

    assert "SECRET" not in json.dumps(manifest.source_query)
    assert manifest.source_query["api_key"] == "***REDACTED***"
    assert manifest.source_query["q"] == "x"
