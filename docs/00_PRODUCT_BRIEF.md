# Product brief

## Product thesis

LitGraph is a literature-review retrieval substrate exposed through MCP. It helps an agent retrieve, expand, and justify paper sets for literature-review workflows over a pre-ingested scientific corpus.

The base product is not an autonomous research scientist and not a general web research agent. It is an offline-built retrieval system with a stable agent-facing interface.

## Base user workflow

A user gives a literature-review request such as:

```text
Find recent papers on retriever training without gold passages.
Filter to ACL, EMNLP, NeurIPS, ICLR, and ICML from 2020 onward.
Group likely papers by method and evaluation setting.
```

The system should support this flow:

```text
query + filters
  -> vector search over precomputed paper/chunk embeddings
  -> seed paper set
  -> citation + metadata graph expansion
  -> ontology graph expansion, once available
  -> ranked result set with provenance
  -> MCP response usable by an agent
```

## Base v1 includes

- Pre-ingested corpus only.
- Raw provider snapshots.
- Canonical paper registry.
- Citation + metadata graph.
- Paper-level embeddings.
- Chunk embeddings where text exists.
- Secure read-only MCP tools.
- Evaluation traces.
- Internal retrieval and ablation benchmarks.
- AstaBench compatibility path for literature-understanding comparisons.

## Base v1 excludes

- Query-time ingestion.
- Periodic retraining.
- Agent write operations.
- Arbitrary graph/database queries through MCP.
- Large frontend.
- General multi-agent orchestration.
- Full PDF parsing for every paper.
- Full AstaBench coverage across all benchmark categories.

## First proof-of-concept corpus

The first corpus should be narrow enough to debug manually. Recommended scope:

```text
Domain: CS/NLP/RAG/retrieval papers
Sources: OpenAlex + Semantic Scholar
Years: configurable, initially recent years
Venues: configurable, initially major NLP/ML venues
```

The corpus is a product decision. It must be recorded as a versioned snapshot before graph or embedding construction.
