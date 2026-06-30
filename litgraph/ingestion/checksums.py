"""SHA-256 checksum helpers used across ingestion and persistence.

Centralized so per-record, per-file, and per-snapshot checksums are all computed
the same way (deterministic, canonical JSON for objects).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    """Return the hex sha256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, *, chunk_size: int = 65536) -> str:
    """Return the hex sha256 digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(chunk_size), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_canonical_json(obj: Any) -> str:
    """Return the hex sha256 digest of an object's canonical JSON encoding."""
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(raw)
