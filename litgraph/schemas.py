"""Core LitGraph schema objects (Stage 0, Task 0.2).

These are the stable, versioned, validated objects that every later milestone
(registry, graph, vector, ontology, MCP) references. This module defines the
data contracts only -- it implements no persistence, normalization,
deduplication, or provider logic.

Invariants enforced here:

- Every schema carries ``schema_version`` (via :class:`SchemaBase`).
- Every corpus object requires ``snapshot_id`` (no default; construction fails
  without it). :class:`EvidenceSpan` is a nested value object and is the sole
  exception -- it is never persisted independently of its claim.
- Provider identifiers (DOI, arXiv, OpenAlex, Semantic Scholar, provider paper
  id) are carried as descriptive fields, never used as internal identity keys.
  Identity keys (``canonical_paper_id``, ``external_record_id``, ...) are
  independent strings.
- Provider names are constrained to the :class:`Provider` enum.

Field contracts follow ``docs/06_DATA_AND_SCHEMA_CONTRACTS.md``.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Version stamped onto every schema instance. Bump deliberately when a
#: persisted contract changes.
SCHEMA_VERSION = "0.1.0"


class Provider(StrEnum):
    """Allowlisted upstream metadata providers (the Stage 1 clients)."""

    OPENALEX = "openalex"
    SEMANTIC_SCHOLAR = "semantic_scholar"


class ClaimStatus(StrEnum):
    """Lifecycle status of an ontology claim."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    FILTERED = "filtered"


class EdgeStatus(StrEnum):
    """Lifecycle status of a materialized ontology edge."""

    ACTIVE = "active"
    RETIRED = "retired"


class SchemaBase(BaseModel):
    """Base for every schema: carries ``schema_version`` and forbids extras."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION


class CorpusObject(SchemaBase):
    """Base for snapshot-scoped persistent objects: requires ``snapshot_id``."""

    snapshot_id: str


class EvidenceSpan(SchemaBase):
    """A character span inside source/evidence text.

    Nested value object (lives inside a claim); intentionally has no
    ``snapshot_id``.
    """

    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    text: str | None = None

    @model_validator(mode="after")
    def _check_offsets(self) -> EvidenceSpan:
        if self.end_offset < self.start_offset:
            raise ValueError("end_offset must be >= start_offset")
        return self


class PaperRecord(CorpusObject):
    """One unmodified provider response plus fetch metadata (raw record).

    The raw payload must not be normalized in place.
    """

    provider: Provider
    provider_record_id: str | None = None
    fetch_run_id: str
    fetched_at: datetime
    raw_payload: dict[str, Any]
    raw_checksum: str


class ExternalRecord(CorpusObject):
    """Provider-specific metadata associated with a canonical paper.

    Provider identifiers are descriptive; ``external_record_id`` is the
    identity key. ``canonical_paper_id`` is populated after registry build.
    """

    external_record_id: str
    provider: Provider
    provider_paper_id: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None
    raw_record_ref: str
    canonical_paper_id: str | None = None


class CanonicalPaper(CorpusObject):
    """Source of truth for paper identity.

    ``canonical_paper_id`` is the internal key; ``doi``/``arxiv_id`` here are
    convenience copies of provider identifiers, not identity keys.
    """

    canonical_paper_id: str
    title: str
    year: int | None = None
    abstract: str | None = None
    venue: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    external_records: list[str] = Field(default_factory=list)


class CitationRecord(CorpusObject):
    """A citation from one canonical paper to another or an unresolved ref."""

    source_canonical_paper_id: str
    target_canonical_paper_id: str | None = None
    unresolved_target_ref: str | None = None
    provider_sources: list[Provider] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_target(self) -> CitationRecord:
        if self.target_canonical_paper_id is None and self.unresolved_target_ref is None:
            raise ValueError(
                "citation requires target_canonical_paper_id or unresolved_target_ref"
            )
        return self


class EmbeddingRecord(CorpusObject):
    """An offline-built embedding for a paper or chunk.

    Embeddings are built offline, never at query time in base v1.
    """

    embedding_id: str
    canonical_paper_id: str
    chunk_id: str | None = None
    vector: list[float] | None = None
    embedding_vector_ref: str | None = None
    embedding_model: str
    embedding_model_version: str
    dimensions: int = Field(gt=0)
    created_at: datetime

    @model_validator(mode="after")
    def _check_vector(self) -> EmbeddingRecord:
        if self.vector is None and self.embedding_vector_ref is None:
            raise ValueError("embedding requires vector or embedding_vector_ref")
        if self.vector is not None and len(self.vector) != self.dimensions:
            raise ValueError("len(vector) must equal dimensions")
        return self


class OntologyEntity(CorpusObject):
    """A normalized ontology entity referenced by ontology edges."""

    entity_id: str
    name: str
    entity_type: str


class OntologyClaim(CorpusObject):
    """An evidence-backed subject-predicate-object claim extracted from a paper."""

    claim_id: str
    canonical_paper_id: str
    chunk_id: str | None = None
    subject_text: str
    subject_type: str
    predicate: str
    object_text: str
    object_type: str
    evidence_text: str
    subject_span: EvidenceSpan
    object_span: EvidenceSpan
    model_version: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: ClaimStatus = ClaimStatus.CANDIDATE


class OntologyEdge(CorpusObject):
    """A materialized ontology edge aggregated from supporting claims.

    No edge may exist without at least one supporting claim.
    """

    ontology_edge_id: str
    subject_entity_id: str
    predicate: str
    object_entity_id: str
    supporting_claim_ids: list[str] = Field(min_length=1)
    supporting_paper_count: int = Field(ge=0)
    mean_confidence: float = Field(ge=0.0, le=1.0)
    max_confidence: float = Field(ge=0.0, le=1.0)
    edge_status: EdgeStatus = EdgeStatus.ACTIVE


class SnapshotManifest(CorpusObject):
    """Manifest describing a persisted snapshot."""

    created_at: datetime
    source: str
    record_count: int = Field(ge=0)
    checksum: str
    description: str | None = None
