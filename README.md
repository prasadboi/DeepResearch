# LitGraph build-control documents

This folder contains the repository documents that should control how Claude Code, GitHub Copilot, or any other coding agent works on the LitGraph proof of concept.

The project should be built one gated task at a time. The coding agent must not infer the next stage and continue building. Each task has a closed product goal, explicit non-goals, programming invariants, construction tests, an evaluation gate, and a human review checkpoint.

## Use order

1. Put `CLAUDE.md` at the repository root if using Claude Code.
2. Put `.github/copilot-instructions.md` in the repository if using GitHub Copilot.
3. Keep `project_control/current_milestone.yaml` updated before starting each task.
4. For every task, copy `docs/10_COPILOT_TASK_PROMPT_TEMPLATE.md` and fill it with the relevant task from `docs/04_TASK_SPECS.md`.
5. Do not authorize the next task until the construction tests and evaluation gate for the current task pass.

## Document map

| File | Purpose |
|---|---|
| `CLAUDE.md` | Operational rules for Claude Code. |
| `.github/copilot-instructions.md` | Operational rules for GitHub Copilot. |
| `docs/00_PRODUCT_BRIEF.md` | Product boundary and proof-of-concept definition. |
| `docs/01_ARCHITECTURE.md` | Architecture: registry, citation graph, vector table, ontology graph, MCP. |
| `docs/02_GLOBAL_INVARIANTS.md` | Invariants that apply to every milestone. |
| `docs/03_MILESTONE_GATES.md` | High-level gated roadmap. |
| `docs/04_TASK_SPECS.md` | Per-task implementation spec. |
| `docs/05_TESTING_AND_EVALUATION.md` | Construction tests vs product evals, ablations, failure rules. |
| `docs/06_DATA_AND_SCHEMA_CONTRACTS.md` | Required data contracts and persistence rules. |
| `docs/07_MCP_TOOL_CONTRACT.md` | MCP tool surface, security, and response guarantees. |
| `docs/08_BENCHMARKING_AND_ASTABENCH_PATH.md` | Internal benchmarking and AstaBench comparison path. |
| `docs/09_CLOUD_AND_OPERATIONS.md` | Cloud promotion, parity, rollback, and recovery. |
| `docs/10_COPILOT_TASK_PROMPT_TEMPLATE.md` | Prompt template for bounded coding tasks. |
| `docs/11_HUMAN_REVIEW_CHECKLIST.md` | Human checkpoints before moving gates. |
| `docs/adr/` | Decision record template and conventions. |
| `tools/validate_docs.py` | Lightweight document quality checker. |

## Current build rule

The next implementation task is not determined by the architecture document. It is determined only by `project_control/current_milestone.yaml` and the approved task prompt derived from `docs/04_TASK_SPECS.md`.

## Safe state definition

These documents are in a safe state when:

- Every stage has at least one task.
- Every task has product goal, inputs, outputs, non-goals, programming invariants, construction tests, evaluation gate, and human checkpoint.
- Evaluation gates avoid unresolved thresholds where a reasonable default can be set now.
- The coding-agent instructions forbid future-stage implementation.
- The validation script passes.
- Known limitations are documented rather than hidden.
