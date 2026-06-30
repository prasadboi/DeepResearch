"""Construction tests for the core schema objects."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import BaseModel, ValidationError

from litgraph.schemas import (
    CanonicalPaper,
    CitationRecord,
    EmbeddingRecord,
    EvidenceSpan,
    ExternalRecord,
    OntologyClaim,
    OntologyEdge,
    OntologyEntity,
    PaperRecord,
    SnapshotManifest,
)

SNAPSHOT = "snap-test"
_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _one_of_each() -> list[BaseModel]:
    """Build one valid instance of every schema class."""
    span = EvidenceSpan(start_offset=0, end_offset=4, text="text")
    return [
        span,
        PaperRecord(
            snapshot_id=SNAPSHOT,
            provider="openalex",
            provider_record_id="W1",
            fetch_run_id="run-1",
            fetched_at=_NOW,
            raw_payload={"id": "W1"},
            raw_checksum="chk-1",
        ),
        ExternalRecord(
            snapshot_id=SNAPSHOT,
            external_record_id="er-1",
            provider="semantic_scholar",
            semantic_scholar_id="S1",
            raw_record_ref="chk-1",
            canonical_paper_id="cp-1",
        ),
        CanonicalPaper(
            snapshot_id=SNAPSHOT,
            canonical_paper_id="cp-1",
            title="A paper",
            external_records=["er-1"],
        ),
        CitationRecord(
            snapshot_id=SNAPSHOT,
            source_canonical_paper_id="cp-1",
            target_canonical_paper_id="cp-2",
            provider_sources=["openalex"],
        ),
        EmbeddingRecord(
            snapshot_id=SNAPSHOT,
            embedding_id="emb-1",
            canonical_paper_id="cp-1",
            vector=[0.0, 1.0],
            embedding_model="m",
            embedding_model_version="0",
            dimensions=2,
            created_at=_NOW,
        ),
        OntologyEntity(
            snapshot_id=SNAPSHOT,
            entity_id="ent-1",
            name="gnn",
            entity_type="method",
        ),
        OntologyClaim(
            snapshot_id=SNAPSHOT,
            claim_id="cl-1",
            canonical_paper_id="cp-1",
            subject_text="gnn",
            subject_type="method",
            predicate="used-for",
            object_text="task",
            object_type="task",
            evidence_text="gnn used for task",
            subject_span=span,
            object_span=EvidenceSpan(start_offset=9, end_offset=17),
            model_version="0",
            confidence=0.5,
        ),
        OntologyEdge(
            snapshot_id=SNAPSHOT,
            ontology_edge_id="edge-1",
            subject_entity_id="ent-1",
            predicate="used-for",
            object_entity_id="ent-2",
            supporting_claim_ids=["cl-1"],
            supporting_paper_count=1,
            mean_confidence=0.5,
            max_confidence=0.5,
        ),
        SnapshotManifest(
            snapshot_id=SNAPSHOT,
            created_at=_NOW,
            source="mock",
            record_count=1,
            checksum="chk",
        ),
    ]


def test_schema_roundtrip_json() -> None:
    for instance in _one_of_each():
        restored = type(instance).model_validate_json(instance.model_dump_json())
        assert restored == instance
        assert instance.schema_version  # every schema carries a version


def test_schema_rejects_missing_snapshot_id() -> None:
    with pytest.raises(ValidationError):
        CanonicalPaper(canonical_paper_id="cp-1", title="A paper")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        PaperRecord(  # type: ignore[call-arg]
            provider="openalex",
            fetch_run_id="run-1",
            fetched_at=_NOW,
            raw_payload={},
            raw_checksum="chk-1",
        )


def test_schema_rejects_invalid_provider_name() -> None:
    with pytest.raises(ValidationError):
        ExternalRecord(
            snapshot_id=SNAPSHOT,
            external_record_id="er-1",
            provider="not_a_provider",  # type: ignore[arg-type]
            raw_record_ref="chk-1",
        )


def test_canonical_id_is_independent_of_provider_ids() -> None:
    paper = CanonicalPaper(
        snapshot_id=SNAPSHOT,
        canonical_paper_id="cp-1",
        title="A paper",
        doi="10.1/abc",
    )
    assert paper.canonical_paper_id != paper.doi
