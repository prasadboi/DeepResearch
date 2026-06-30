# MCP tool contract

## Role of MCP

MCP is the stable abstraction over the three internal structures:

```text
citation + metadata graph
vector embedding search table
ontology claim graph
```

The agent should call MCP tools only. It should not know which database or storage system backs a result.

## Security rules

- Tools are allowlisted.
- Tools are read-only in base v1.
- Tools require authentication in non-local mode.
- No arbitrary Cypher, SQL, Python, shell, or provider API passthrough.
- Every input schema is validated before execution.
- Every tool has a depth, top_k, or result-size bound where applicable.
- Every tool call is logged with request_id and latency.

## Tool rollout

### MCP v0: citation and metadata graph tools

```text
get_paper(paper_id)
search_papers_by_metadata(filters)
expand_citations(paper_id, direction, depth, filters)
get_paper_neighborhood(paper_id, depth, filters)
```

### MCP v1: embedding/search tools

```text
hybrid_search(query, filters, top_k)
get_relevant_chunks(query, filters, top_k)
search_then_expand(query, filters, expansion_config)
```

### MCP v2: ontology tools

```text
get_claims_for_paper(paper_id)
get_ontology_edges_for_paper(paper_id)
expand_by_ontology(entity_id, relation_types, depth)
explain_ontology_edge(edge_id)
```

## Response requirements

Every paper result must include:

```text
canonical_paper_id
title when available
year when available
venue when available
retrieval_source: seed | citation_expansion | ontology_expansion | metadata
retrieval_reason
score optional
provenance
```

Every chunk result must include:

```text
chunk_id
canonical_paper_id
text or excerpt
score
source offsets when available
provenance
```

Every ontology edge explanation must include:

```text
edge
supporting_claims
supporting_paper_count
mean_confidence
max_confidence
model_version or model_versions
```

## Error requirements

Errors must be typed and safe. Examples:

```text
UNKNOWN_PAPER_ID
INVALID_FILTER
UNAVAILABLE_FILTER_VALUE
DEPTH_LIMIT_EXCEEDED
UNAUTHORIZED
TOOL_NOT_ALLOWED
SNAPSHOT_NOT_AVAILABLE
BACKEND_UNAVAILABLE
```

Do not return stack traces through MCP responses.
