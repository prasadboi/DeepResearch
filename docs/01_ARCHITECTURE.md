# Architecture

## High-level shape

```text
External paper APIs
  -> raw snapshots
  -> canonical paper registry
  -> citation + metadata graph

Canonical paper registry
  -> embedding pipeline
  -> vector search table

Canonical paper registry + chunks
  -> ontology extraction pipeline
  -> claims with evidence spans
  -> materialized ontology edges

MCP server
  -> read-only tools over graph, vector search, and ontology
  -> agent-facing literature graph interface
```

## The three retrieval substrates

### 1. Citation + metadata graph

Built offline from normalized paper metadata and citation records.

Minimum graph:

```text
(Paper)-[:CITES]->(Paper)
(Paper)-[:AUTHORED_BY]->(Author)
(Paper)-[:PUBLISHED_IN]->(Venue)
(Paper)-[:HAS_EXTERNAL_RECORD]->(ExternalRecord)
```

This graph supports expansion, neighborhood inspection, and metadata filtering. It is not built at query time.

### 2. Vector embedding search table

Built offline from canonical papers and chunks.

Minimum searchable records:

```text
Paper title + abstract embedding
Chunk embedding where chunk text exists
```

Every embedding record must reference `canonical_paper_id`, `snapshot_id`, `embedding_model`, `embedding_model_version`, and dimensionality.

### 3. Ontology claim graph

Built from a supervised extraction pipeline, not by storing raw LLM-generated edges.

The extractor emits:

```text
Claim(subject entity, relation, object entity, evidence span, confidence, model version)
```

Materialized ontology edges are aggregates over Claims. Every ontology edge must be explainable through supporting Claims and evidence spans.

## Canonical paper registry

The registry is the identity source of truth.

```text
raw provider records
  -> normalized paper candidates
  -> deduplicated canonical papers
  -> stable canonical_paper_id
```

Provider IDs are external identifiers. They must not become internal primary keys for graph, vector, ontology, or MCP layers.

## MCP as the product boundary

The MCP server exposes one coherent literature graph interface over the internal structures.

The agent sees tools like:

```text
get_paper
expand_citations
hybrid_search
search_then_expand
get_claims_for_paper
explain_ontology_edge
```

The agent must not know or access:

```text
Neo4j internals
vector DB internals
provider APIs
raw storage paths
model artifact paths
arbitrary database query languages
```

## Data flow at query time

No ingestion occurs at query time.

```text
User query
  -> MCP search tool
  -> vector search over precomputed index
  -> graph expansion over prebuilt graph
  -> optional ontology expansion over prebuilt ontology edges
  -> result ranking and provenance bundle
```

If a requested conference, time range, or source is unavailable in the current snapshot, the system returns a typed no-result or unavailable-filter response. It does not fetch new data on the fly.

## Local-cloud parity

Every major structure must be buildable locally first and then promoted to cloud:

```text
local raw snapshot -> cloud raw snapshot
local graph -> cloud graph
local vector index -> cloud vector index
local ontology graph -> cloud ontology graph
```

Cloud behavior must match local behavior for the same `snapshot_id` and `schema_version` within declared tolerances.
