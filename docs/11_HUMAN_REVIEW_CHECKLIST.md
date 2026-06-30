# Human review checklist

Use this checklist before authorizing the next task.

## Universal checkpoint

- [ ] Active task in `project_control/current_milestone.yaml` matches the work performed.
- [ ] Construction tests passed.
- [ ] Evaluation gate passed or a deliberate stop decision was recorded.
- [ ] Non-goals were not implemented.
- [ ] Global invariants were not violated.
- [ ] New design decisions were recorded as ADRs.
- [ ] Artifacts include `snapshot_id` and `schema_version` where applicable.
- [ ] Logs contain enough information to debug failures.
- [ ] Secrets are not present in code, config, fixtures, docs, or logs.

## Stage-specific focus

### Stage 1: raw ingestion

- [ ] Raw payloads are not mutated.
- [ ] Snapshot manifests and checksums are valid.
- [ ] Cloud upload does not overwrite without explicit force.

### Stage 2: registry

- [ ] Review at least 20 dedup merge samples, or all samples if fewer than 20; none may merge clearly different titles with different years unless an ADR allows that rule.
- [ ] Review at least 20 high-similarity non-merge samples, or all samples if fewer than 20; false non-merges that share DOI or arXiv ID must be fixed before proceeding.
- [ ] Canonical IDs are stable.
- [ ] Registry report indicates corpus quality is sufficient for graph work.

### Stage 3: graph

- [ ] Graph is idempotent on rerun.
- [ ] Unresolved citations are reported.
- [ ] Diagnostics do not show unacceptable duplication or orphaning.

### Stage 5: MCP graph server

- [ ] Unauthorized requests fail closed.
- [ ] No arbitrary backend query tool exists.
- [ ] Logs are safe and useful.

### Stage 6-8: embeddings and search

- [ ] Retrieval beats simple baseline.
- [ ] Filters are correct.
- [ ] Results include provenance.
- [ ] Search-then-expand does not create duplicate papers.

### Stage 9-11: ontology

- [ ] Dataset adapters validate offsets and labels.
- [ ] Claims have evidence spans.
- [ ] Ontology edges have supporting claims.
- [ ] MCP explanations are evidence-backed.

### Stage 12: benchmark hardening

- [ ] Ablations are generated.
- [ ] AstaBench comparison logs are complete.
- [ ] Claims about improvement are supported by metrics.
