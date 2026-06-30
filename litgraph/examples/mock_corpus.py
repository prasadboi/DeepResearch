"""Mock corpus fixture loader and fake-flow verifier (Stage 0, Task 0.2).

Loads the shipped synthetic corpus into validated schema objects and checks
that the references between layers resolve end to end:

    raw record -> canonical paper -> citation -> embedding record -> ontology claim

No persistence, normalization, or provider logic is involved; this only proves
the schema contracts compose into a coherent fake flow.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from litgraph.schemas import (
    CanonicalPaper,
    CitationRecord,
    EmbeddingRecord,
    ExternalRecord,
    OntologyClaim,
    OntologyEdge,
    OntologyEntity,
    PaperRecord,
    SnapshotManifest,
)

#: Default fixture shipped as package data.
DEFAULT_CORPUS_RESOURCE = files("litgraph.examples").joinpath("data/mock_corpus.json")


class MockCorpus(BaseModel):
    """A fully validated in-memory mock corpus."""

    model_config = ConfigDict(extra="forbid")

    snapshot_manifest: SnapshotManifest
    paper_records: list[PaperRecord]
    external_records: list[ExternalRecord]
    canonical_papers: list[CanonicalPaper]
    citation_records: list[CitationRecord]
    embedding_records: list[EmbeddingRecord]
    ontology_entities: list[OntologyEntity]
    ontology_claims: list[OntologyClaim]
    ontology_edges: list[OntologyEdge]


def load_mock_corpus(path: Path | None = None) -> MockCorpus:
    """Load and validate the mock corpus from JSON.

    Args:
        path: Optional explicit path to a corpus JSON file. Defaults to the
            packaged fixture.

    Returns:
        A validated :class:`MockCorpus`.
    """
    if path is None:
        raw = DEFAULT_CORPUS_RESOURCE.read_text(encoding="utf-8")
    else:
        raw = Path(path).read_text(encoding="utf-8")
    return MockCorpus.model_validate_json(raw)


def verify_fake_flow(corpus: MockCorpus) -> None:
    """Verify the cross-layer references of the corpus resolve.

    Raises:
        ValueError: if any reference in the
            raw -> canonical -> citation -> embedding -> claim flow is broken.
    """
    snapshot_ids = {
        corpus.snapshot_manifest.snapshot_id,
        *(r.snapshot_id for r in corpus.paper_records),
        *(c.snapshot_id for c in corpus.canonical_papers),
    }
    if len(snapshot_ids) != 1:
        raise ValueError(f"corpus spans multiple snapshot_ids: {sorted(snapshot_ids)}")

    canonical_ids = {p.canonical_paper_id for p in corpus.canonical_papers}
    if not canonical_ids:
        raise ValueError("corpus has no canonical papers")

    # raw record -> canonical paper: every external record links a raw record to
    # a known canonical paper.
    raw_refs = {r.raw_checksum for r in corpus.paper_records}
    for ext in corpus.external_records:
        if ext.raw_record_ref not in raw_refs:
            raise ValueError(f"external record {ext.external_record_id} has no raw record")
        if ext.canonical_paper_id is not None and ext.canonical_paper_id not in canonical_ids:
            raise ValueError(
                f"external record {ext.external_record_id} points to unknown canonical paper"
            )

    # citation -> canonical papers.
    has_citation = False
    for cit in corpus.citation_records:
        if cit.source_canonical_paper_id not in canonical_ids:
            raise ValueError("citation source is not a known canonical paper")
        if cit.target_canonical_paper_id is not None:
            if cit.target_canonical_paper_id not in canonical_ids:
                raise ValueError("citation target is not a known canonical paper")
            has_citation = True
    if not has_citation:
        raise ValueError("corpus has no resolved citation between canonical papers")

    # embedding record -> canonical paper.
    if not corpus.embedding_records:
        raise ValueError("corpus has no embedding records")
    for emb in corpus.embedding_records:
        if emb.canonical_paper_id not in canonical_ids:
            raise ValueError(f"embedding {emb.embedding_id} references unknown canonical paper")

    # ontology claim -> canonical paper; ontology edge -> claims + entities.
    if not corpus.ontology_claims:
        raise ValueError("corpus has no ontology claims")
    claim_ids = {c.claim_id for c in corpus.ontology_claims}
    for claim in corpus.ontology_claims:
        if claim.canonical_paper_id not in canonical_ids:
            raise ValueError(f"claim {claim.claim_id} references unknown canonical paper")

    entity_ids = {e.entity_id for e in corpus.ontology_entities}
    for edge in corpus.ontology_edges:
        if not set(edge.supporting_claim_ids) <= claim_ids:
            raise ValueError(f"edge {edge.ontology_edge_id} references unknown supporting claim")
        if edge.subject_entity_id not in entity_ids or edge.object_entity_id not in entity_ids:
            raise ValueError(f"edge {edge.ontology_edge_id} references unknown entity")


def summarize(corpus: MockCorpus) -> dict[str, int]:
    """Return per-schema record counts for reporting."""
    return {
        "snapshot_manifest": 1,
        "paper_records": len(corpus.paper_records),
        "external_records": len(corpus.external_records),
        "canonical_papers": len(corpus.canonical_papers),
        "citation_records": len(corpus.citation_records),
        "embedding_records": len(corpus.embedding_records),
        "ontology_entities": len(corpus.ontology_entities),
        "ontology_claims": len(corpus.ontology_claims),
        "ontology_edges": len(corpus.ontology_edges),
    }
