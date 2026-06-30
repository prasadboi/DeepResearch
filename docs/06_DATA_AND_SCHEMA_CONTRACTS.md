# Data and schema contracts

This file describes the minimum persistent objects. Exact implementation may use Pydantic, dataclasses, SQL tables, graph nodes, JSONL records, or another typed representation, but the contracts must be preserved.

## Shared required fields

Persistent objects should include:

```text
schema_version
snapshot_id
created_at where relevant
source or producer where relevant
```

## Raw provider record

Represents one unmodified provider response plus fetch metadata.

Required fields:

```text
provider
provider_record_id when available
snapshot_id
fetch_run_id
fetched_at
raw_payload
raw_checksum
```

Invariant: raw payload must not be normalized in place.

## ExternalRecord

Represents provider-specific metadata associated with a canonical paper.

Required fields:

```text
external_record_id
provider
provider_paper_id when available
doi when available
arxiv_id when available
openalex_id when available
semantic_scholar_id when available
raw_record_ref
canonical_paper_id after registry build
```

Invariant: one ExternalRecord maps to at most one canonical paper.

## CanonicalPaper

Source of truth for paper identity.

Required fields:

```text
canonical_paper_id
title
year optional
abstract optional
venue optional
doi optional
arxiv_id optional
external_records
snapshot_id
schema_version
```

Invariant: graph, vector, ontology, and MCP layers reference this ID.

## CitationRecord

Represents a citation from one canonical paper to another, or to an unresolved external reference.

Required fields:

```text
source_canonical_paper_id
target_canonical_paper_id optional
unresolved_target_ref optional
provider_sources
snapshot_id
```

Invariant: unresolved citations are reported, not silently dropped.

## Chunk

Represents text used for embeddings and ontology inference.

Required fields:

```text
chunk_id
canonical_paper_id
text
start_offset optional
end_offset optional
chunking_config_hash
snapshot_id
```

Invariant: chunk IDs are stable for the same paper text and chunking config.

## EmbeddingRecord

Required fields:

```text
embedding_id
canonical_paper_id
chunk_id optional
embedding_vector_ref or vector
embedding_model
embedding_model_version
dimensions
created_at
snapshot_id
```

Invariant: embeddings are built offline, not at query time in base v1.

## OntologyClaim

Required fields:

```text
claim_id
canonical_paper_id
chunk_id optional
subject_text
subject_type
predicate
object_text
object_type
evidence_text
subject_span
object_span
model_version
confidence
status
snapshot_id
```

Invariant: every claim has evidence and model provenance.

## OntologyEdge

Required fields:

```text
ontology_edge_id
subject_entity_id
predicate
object_entity_id
supporting_claim_ids
supporting_paper_count
mean_confidence
max_confidence
edge_status
snapshot_id
```

Invariant: no ontology edge exists without at least one supporting claim.

## MCP response envelope

Every MCP tool response should include:

```text
request_id
snapshot_id
tool_name
result
provenance
warnings
error optional
```

Invariant: user-facing results must be explainable through provenance.

## Deterministic graph count mapping rules

When comparing registry and graph counts during Stage 3 and Stage 4:

- One `CanonicalPaper` maps to exactly one `Paper` node.
- One unique normalized author identity maps to at most one `Author` node. If no author identity is available, the author is not materialized and must be counted in diagnostics.
- One unique normalized venue identity maps to at most one `Venue` node. If no venue identity is available, the venue is not materialized and must be counted in diagnostics.
- One `ExternalRecord` maps to exactly one `ExternalRecord` node or equivalent provider-record representation.
- One resolved citation maps to at most one `CITES` edge. Duplicate provider evidence is stored as properties/support, not duplicate edges.
- Unresolved citations are represented in diagnostics or unresolved-reference storage, not silently discarded.

