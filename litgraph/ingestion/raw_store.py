"""Local raw snapshot store (Stage 1, Task 1.2).

Persists raw provider records (`PaperRecord`) as **append-only** JSONL, one file
per provider, each with an `IngestionManifest`, plus one `SnapshotManifest` per
snapshot. Snapshots are immutable: an existing snapshot is never overwritten
unless ``force=True`` (logged). Reading and validation recompute record counts
and file checksums and compare them to the manifests.

No normalization, identity creation, deduplication, or cloud upload happens here.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from litgraph.ingestion.checksums import sha256_canonical_json, sha256_file
from litgraph.schemas import IngestionManifest, PaperRecord, Provider, SnapshotManifest

logger = logging.getLogger(__name__)

_SNAPSHOT_MANIFEST_NAME = "snapshot.manifest.json"
_MANIFEST_SUFFIX = ".manifest.json"
_REDACTED = "***REDACTED***"
_SECRET_KEY_SUBSTRINGS = (
    "api_key",
    "api-key",
    "apikey",
    "authorization",
    "token",
    "secret",
    "password",
)


class RawStoreError(Exception):
    """Base error for the raw snapshot store."""


class SnapshotExistsError(RawStoreError):
    """Raised when writing a snapshot that already exists without ``force``."""


class SnapshotValidationError(RawStoreError):
    """Raised when a snapshot cannot be read or is structurally invalid."""


@dataclass
class SnapshotValidationReport:
    """Result of validating a snapshot's counts and checksums."""

    snapshot_id: str
    ok: bool
    issues: list[str] = field(default_factory=list)


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in _SECRET_KEY_SUBSTRINGS)


def _sanitize(value: Any) -> Any:
    """Recursively replace secret-looking values so they are never persisted."""
    if isinstance(value, Mapping):
        return {
            k: (_REDACTED if _is_secret_key(str(k)) else _sanitize(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _provider_source_query(source_query: Mapping[Any, Any] | None, provider: Provider) -> dict:
    if not source_query:
        return {}
    if all(isinstance(key, Provider) for key in source_query):
        return dict(source_query.get(provider, {}))
    return dict(source_query)


class RawSnapshotStore:
    """Reads and writes immutable local raw snapshots under ``raw_root``."""

    def __init__(self, raw_root: Path) -> None:
        self._root = Path(raw_root)

    def snapshot_dir(self, snapshot_id: str) -> Path:
        return self._root / snapshot_id

    # -- write -----------------------------------------------------------

    def write_snapshot(
        self,
        snapshot_id: str,
        records_by_provider: Mapping[Provider, Sequence[PaperRecord]],
        *,
        source_query: Mapping[Any, Any] | None = None,
        fetch_run_id: str | None = None,
        force: bool = False,
    ) -> SnapshotManifest:
        snap_dir = self.snapshot_dir(snapshot_id)
        manifest_path = snap_dir / _SNAPSHOT_MANIFEST_NAME
        already_exists = manifest_path.exists()
        if already_exists and not force:
            raise SnapshotExistsError(
                f"snapshot {snapshot_id!r} already exists at {snap_dir}; "
                "pass force=True to overwrite"
            )

        snap_dir.mkdir(parents=True, exist_ok=True)
        mode = "w" if force else "x"

        ingestion_manifests: list[IngestionManifest] = []
        manifest_refs: list[str] = []
        providers: list[Provider] = []
        total = 0
        now = datetime.now(UTC)

        for provider, records in records_by_provider.items():
            run_id = self._validate_records(snapshot_id, provider, records, fetch_run_id)
            file_name = f"{provider.value}.jsonl"
            self._write_jsonl(snap_dir / file_name, records, mode)
            manifest = IngestionManifest(
                snapshot_id=snapshot_id,
                provider=provider,
                fetch_run_id=run_id,
                created_at=now,
                record_count=len(records),
                file=file_name,
                checksum=sha256_file(snap_dir / file_name),
                source_query=_sanitize(_provider_source_query(source_query, provider)),
            )
            manifest_name = f"{provider.value}{_MANIFEST_SUFFIX}"
            self._write_text(snap_dir / manifest_name, manifest.model_dump_json(indent=2), mode)
            ingestion_manifests.append(manifest)
            manifest_refs.append(manifest_name)
            providers.append(provider)
            total += len(records)

        snapshot = SnapshotManifest(
            snapshot_id=snapshot_id,
            created_at=now,
            source="raw_ingestion",
            record_count=total,
            total_record_count=total,
            checksum=_aggregate_checksum(ingestion_manifests),
            description=f"Raw snapshot with {len(providers)} provider file(s).",
            providers=providers,
            ingestion_manifests=manifest_refs,
        )
        self._write_text(manifest_path, snapshot.model_dump_json(indent=2), mode)

        if already_exists and force:
            logger.warning("force-overwrote existing raw snapshot %r at %s", snapshot_id, snap_dir)
        else:
            logger.info("wrote raw snapshot %r (%d records) at %s", snapshot_id, total, snap_dir)
        return snapshot

    # -- read ------------------------------------------------------------

    def read_snapshot_manifest(self, snapshot_id: str) -> SnapshotManifest:
        path = self.snapshot_dir(snapshot_id) / _SNAPSHOT_MANIFEST_NAME
        if not path.exists():
            raise SnapshotValidationError(f"snapshot manifest not found: {path}")
        return SnapshotManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def read_ingestion_manifest(self, snapshot_id: str, provider: Provider) -> IngestionManifest:
        path = self.snapshot_dir(snapshot_id) / f"{provider.value}{_MANIFEST_SUFFIX}"
        if not path.exists():
            raise SnapshotValidationError(f"ingestion manifest not found: {path}")
        return IngestionManifest.model_validate_json(path.read_text(encoding="utf-8"))

    def iter_records(self, snapshot_id: str, provider: Provider) -> Iterator[PaperRecord]:
        path = self.snapshot_dir(snapshot_id) / f"{provider.value}.jsonl"
        if not path.exists():
            raise SnapshotValidationError(f"raw JSONL not found: {path}")
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield PaperRecord.model_validate_json(line)

    # -- validate --------------------------------------------------------

    def validate_snapshot(self, snapshot_id: str) -> SnapshotValidationReport:
        snap_dir = self.snapshot_dir(snapshot_id)
        issues: list[str] = []
        snapshot = self.read_snapshot_manifest(snapshot_id)

        manifests: list[IngestionManifest] = []
        counted_total = 0
        for ref in snapshot.ingestion_manifests:
            manifest = IngestionManifest.model_validate_json(
                (snap_dir / ref).read_text(encoding="utf-8")
            )
            manifests.append(manifest)
            jsonl_path = snap_dir / manifest.file
            if not jsonl_path.exists():
                issues.append(f"missing JSONL file: {manifest.file}")
                continue
            actual_checksum = sha256_file(jsonl_path)
            if actual_checksum != manifest.checksum:
                issues.append(f"checksum mismatch for {manifest.file}")
            actual_count = _count_lines(jsonl_path)
            if actual_count != manifest.record_count:
                issues.append(
                    f"record_count mismatch for {manifest.file}: "
                    f"manifest={manifest.record_count} actual={actual_count}"
                )
            counted_total += actual_count

        if snapshot.total_record_count != counted_total:
            issues.append(
                f"total_record_count mismatch: manifest={snapshot.total_record_count} "
                f"actual={counted_total}"
            )
        if snapshot.checksum != _aggregate_checksum(manifests):
            issues.append("snapshot aggregate checksum mismatch")

        return SnapshotValidationReport(snapshot_id=snapshot_id, ok=not issues, issues=issues)

    # -- helpers ---------------------------------------------------------

    def _validate_records(
        self,
        snapshot_id: str,
        provider: Provider,
        records: Sequence[PaperRecord],
        fetch_run_id: str | None,
    ) -> str:
        if not records:
            raise RawStoreError(f"no records to write for provider {provider}")
        run_ids = set()
        for record in records:
            if record.snapshot_id != snapshot_id:
                raise RawStoreError(
                    f"record snapshot_id {record.snapshot_id!r} != snapshot {snapshot_id!r}"
                )
            if record.provider != provider:
                raise RawStoreError(
                    f"record provider {record.provider} != target provider {provider}"
                )
            if "canonical_paper_id" in record.raw_payload:
                raise RawStoreError("raw payload must not contain canonical_paper_id")
            run_ids.add(record.fetch_run_id)
        if fetch_run_id is not None:
            return fetch_run_id
        if len(run_ids) != 1:
            raise RawStoreError(f"records for {provider} span multiple fetch_run_ids: {run_ids}")
        return run_ids.pop()

    def _write_jsonl(self, path: Path, records: Sequence[PaperRecord], mode: str) -> None:
        try:
            with path.open(mode, encoding="utf-8") as handle:
                for record in records:
                    handle.write(record.model_dump_json() + "\n")
        except FileExistsError as exc:
            raise SnapshotExistsError(f"raw file already exists: {path}") from exc

    def _write_text(self, path: Path, text: str, mode: str) -> None:
        try:
            with path.open(mode, encoding="utf-8") as handle:
                handle.write(text)
        except FileExistsError as exc:
            raise SnapshotExistsError(f"file already exists: {path}") from exc


def _aggregate_checksum(manifests: Sequence[IngestionManifest]) -> str:
    payload = [
        {
            "provider": m.provider.value,
            "file": m.file,
            "checksum": m.checksum,
            "record_count": m.record_count,
        }
        for m in sorted(manifests, key=lambda m: m.provider.value)
    ]
    return sha256_canonical_json(payload)


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())
