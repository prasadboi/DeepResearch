# Testing and evaluation strategy

## Two kinds of tests

### Construction tests

Construction tests prove that the code solves the bounded programming problem for the current task.

Rules:

- Use small fixtures.
- Do not depend on corpus size.
- Do not require live external APIs.
- Do not require cloud unless the task itself is a cloud task.
- Must be deterministic.
- Must be runnable in CI.

Examples:

```text
test_exact_doi_merge
test_chunk_ids_stable
test_mcp_rejects_unknown_tool
test_edge_requires_supporting_claim
```

### Evaluation gates

Evaluation gates prove that the product behavior at the current stage is good enough to proceed.

Rules:

- May use real snapshots.
- May use cloud resources for cloud stages.
- May use benchmark subsets.
- Must produce reports.
- Failure blocks the next task.

Examples:

```text
registry_report.md
graph_diagnostics.md
retrieval_ablation_report.json
mcp_security_eval.json
astabench_smoke_trace.jsonl
```


## Default PoC thresholds

These defaults make evaluation gates closed rather than open-ended. Change them only through an ADR or an explicit task update.

| Area | Default threshold |
|---|---:|
| Filter correctness on scripted retrieval evals | 100% |
| Duplicate canonical paper IDs in result set | 0 |
| Embedding search improvement over metadata-only Recall@20 | at least +0.01 |
| Search-then-expand Recall@20 vs embedding-only | no regression |
| Hosted search Recall@20 vs local | no worse than -0.02 |
| Hosted scripted search p95 latency | <= 5 seconds |
| Cloud/local vector search Jaccard@20 | >= 0.80 |
| Claim evidence-span coverage | 100% |
| Claim sampled precision for PoC | >= 0.70 over at least 30 claims, or all claims if fewer exist |
| Unsupported ontology edges | 0 |
| Provenance coverage for user-facing results | 100% |
| Unauthorized MCP scripted calls rejected | 100% |

## Failure policy

| Result | Action |
|---|---|
| Construction tests fail | Fix code. Do not run product eval as a substitute. |
| Construction tests pass, eval gate fails | Debug product behavior. Do not proceed. |
| Eval gate passes with known limitations | Record accepted risks at the human checkpoint. |
| Task requires a new design decision | Stop and write or update an ADR before coding further. |

## Required evaluation families

### Registry quality

- Raw records by provider.
- Normalized count.
- Rejection count by reason.
- Duplicate merge count.
- Missing DOI rate.
- Missing abstract rate.
- Year and venue distributions.

### Graph quality

- Paper node count.
- Citation edge count.
- Unresolved citation count.
- Orphan paper count.
- Duplicate external identifier count.
- Largest connected components.

### Retrieval quality

Maintain a curated query set for internal evaluation.

Minimum metrics:

```text
Recall@10
Recall@20
MRR
nDCG@10
filter correctness
duplicate canonical_paper_id rate
latency
```

### Ontology quality

Minimum metrics:

```text
entity F1
relation F1
claim precision from sampled audit
evidence-span coverage
invalid-edge rate
unsupported-edge rate
confidence distribution sanity
```

### MCP quality

Minimum metrics:

```text
tool-call success rate
auth rejection correctness
schema validation correctness
provenance coverage
latency
error type coverage
```

## Ablation policy

From Stage 6 onward, run ablations whenever possible:

```text
metadata only
embedding only
citation expansion only
embedding + citation graph
embedding + citation graph + ontology
```

The project should eventually prove which layer improves literature-review performance, not merely show that the full system works.

## Product evaluation threshold style

Avoid pretending early thresholds are final research claims. Use stage-appropriate gates:

- Early gates: sanity, correctness, and no regressions.
- Middle gates: beats simple baseline.
- Late gates: ablation improvement and benchmark comparison.

All thresholds must be recorded in the eval config so they can be changed deliberately rather than implicitly.
