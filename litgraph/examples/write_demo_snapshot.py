"""Write and validate a local raw snapshot from offline provider output (Task 1.2).

Builds offline raw records (reusing the smoke-ingest replay path — no network),
writes them to ``config.raw_dir`` as an immutable snapshot with per-provider
``IngestionManifest``s and a ``SnapshotManifest``, then validates the snapshot
(record counts + checksums) and prints a summary.

Run with::

    python -m litgraph.examples.write_demo_snapshot
    python -m litgraph.examples.write_demo_snapshot --snapshot-id demo-0002 --force
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from litgraph.config import load_config
from litgraph.examples.smoke_ingest import run_offline
from litgraph.ingestion.base import FetchContext
from litgraph.ingestion.raw_store import RawSnapshotStore, SnapshotExistsError
from litgraph.schemas import PaperRecord, Provider

DEFAULT_SNAPSHOT_ID = "demo-0001"


def _records_by_provider(
    records: dict[str, list[PaperRecord]],
) -> dict[Provider, list[PaperRecord]]:
    grouped: dict[Provider, list[PaperRecord]] = {}
    for provider_records in records.values():
        for record in provider_records:
            grouped.setdefault(record.provider, []).append(record)
    return grouped


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a local raw snapshot (offline demo)")
    parser.add_argument("--snapshot-id", default=DEFAULT_SNAPSHOT_ID)
    parser.add_argument("--force", action="store_true", help="overwrite an existing snapshot")
    args = parser.parse_args(argv)

    config = load_config()
    ctx = FetchContext(snapshot_id=args.snapshot_id, fetch_run_id=f"{args.snapshot_id}-run")
    grouped = _records_by_provider(run_offline(ctx))

    # A representative source-query record; the api_key shows secret sanitization.
    source_query = {
        "mode": "offline-demo",
        "query": "graphs",
        "api_key": "fake-secret-should-redact",
    }

    store = RawSnapshotStore(config.raw_dir)
    try:
        snapshot = store.write_snapshot(
            args.snapshot_id, grouped, source_query=source_query, force=args.force
        )
    except SnapshotExistsError as exc:
        print(f"[write_demo_snapshot] refused: {exc}")
        return 1

    report = store.validate_snapshot(args.snapshot_id)
    snap_dir = store.snapshot_dir(args.snapshot_id)

    print(f"[write_demo_snapshot] snapshot_id={snapshot.snapshot_id} dir={snap_dir}")
    print(
        f"[write_demo_snapshot] providers={[p.value for p in snapshot.providers]} "
        f"total_record_count={snapshot.total_record_count} checksum={snapshot.checksum[:12]}..."
    )
    for provider in snapshot.providers:
        manifest = store.read_ingestion_manifest(args.snapshot_id, provider)
        print(
            f"[write_demo_snapshot]   {provider.value}: file={manifest.file} "
            f"records={manifest.record_count} checksum={manifest.checksum[:12]}... "
            f"source_query={manifest.source_query}"
        )
    print(f"[write_demo_snapshot] validation ok={report.ok} issues={report.issues}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
