# Document self-review report

## Review method

I created the repository guidance documents, then reviewed them against the requirements:

1. Each stage needs a closed product goal.
2. Each task needs programming invariants.
3. Each task needs construction tests independent of corpus size.
4. Each task needs a product evaluation gate.
5. Copilot and Claude Code must be prevented from building future stages.
6. Evaluation gates should not leave avoidable thresholds undefined.

I also ran `tools/validate_docs.py`, which checks required files, task sections, and key global terms.

## Iteration 1 findings

Validation passed structurally, but critical review found issues:

- Some evaluation gates used vague phrases such as `chosen p95 latency budget`, `sane edge count`, `highly overlapping top-k`, and `above chosen PoC threshold`.
- Human review language for deduplication used `reasonable`, which was not specific enough.
- The data contract did not explicitly define how registry counts should map to graph counts during parity checks.
- The document set did not define what counts as a safe state.

## Fixes applied

- Added default PoC thresholds in `docs/05_TESTING_AND_EVALUATION.md`.
- Replaced vague evaluation gates in `docs/04_TASK_SPECS.md` with concrete thresholds, including:
  - cloud/local vector Jaccard@20 >= 0.80,
  - hosted search p95 latency <= 5 seconds,
  - claim sampled precision >= 0.70 over at least 30 claims,
  - ontology sampled edge explanations over at least 20 edges,
  - full-system Recall@20 no worse than embedding-only Recall@20.
- Added deterministic graph count mapping rules to `docs/06_DATA_AND_SCHEMA_CONTRACTS.md`.
- Replaced vague dedup review checklist items with sample-count requirements and explicit failure conditions.
- Added a safe-state definition to `README.md`.

## Iteration 2 findings

A second scan found no remaining ambiguous gate terms that would block implementation. The only remaining occurrences of words like `chosen` or `open-ended` are explanatory text in the ADR template and threshold-policy section, not task gates.

## Final validation

- Required files present: yes.
- Stage count in task specs: 13.
- Task count in task specs: 30.
- Every task has required sections: yes.
- Key global terms present: yes.
- Validation command: `python tools/validate_docs.py`.
- Validation result: pass.

## Remaining known limitations

These are acceptable for a safe starting state:

- Exact tech stack choices are intentionally not fixed here. They should be decided in ADRs when implementation begins.
- Exact first corpus size and venue list are not fixed here. They should be set in corpus config during ingestion planning.
- AstaBench integration is specified as a compatibility path and smoke adapter first, not a full benchmark implementation in early milestones.
- Ontology model architecture is not fixed beyond the claim/evidence contract because the research paper review is still in progress.

## Safe state conclusion

The documents are safe to place in a repository and use as build-control instructions for Claude Code or GitHub Copilot. They constrain coding agents to one task at a time, define construction tests separately from product evaluation gates, and preserve the staged architecture.
