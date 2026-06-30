# Benchmarking and AstaBench path

## Purpose

The project needs two forms of evidence:

1. Internal evidence that each layer works.
2. External comparison showing how an agent using LitGraph MCP performs on literature-understanding benchmarks.

## Internal benchmark first

Before running a full external benchmark, maintain a small curated evaluation set:

```text
20-50 literature-review queries
gold relevant paper IDs
optional gold chunk IDs
filters such as year and venue
```

Run retrieval ablations:

```text
metadata only
embedding only
citation expansion only
embedding + citation graph
embedding + citation graph + ontology
```

Minimum metrics:

```text
Recall@10
Recall@20
MRR
nDCG@10
filter correctness
provenance coverage
duplicate rate
latency
```

## AstaBench compatibility path

AstaBench should be treated as a planned comparison target, not merely inspiration.

The project should add an adapter after MCP search tools exist:

```text
evals/astabench/litgraph_solver.py
evals/astabench/mcp_client_adapter.py
evals/astabench/configs/
```

The adapter must call MCP tools only. It must not bypass the product interface to access databases directly.

## Scope of first AstaBench work

The first target should be literature-understanding style tasks. The project should not initially optimize for unrelated benchmark categories such as code execution or full autonomous discovery workflows.

Stage 8 should run only a smoke adapter. Stage 12 should run a meaningful comparison.

## Comparison design

At Stage 12, compare:

```text
baseline agent without LitGraph MCP
agent + MCP embeddings only
agent + MCP embeddings + citation graph
agent + MCP embeddings + citation graph + ontology
```

Record:

```text
benchmark/task name
agent/model config
snapshot_id
MCP tools available
tool-call trace
scores
cost
latency
failures
```

## Interpretation rule

Do not claim the system is better because the full stack works on a demo. Claim improvement only when ablations show a measurable gain and logs are complete enough to audit.
