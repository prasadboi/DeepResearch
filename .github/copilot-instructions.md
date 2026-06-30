# GitHub Copilot instructions for LitGraph

This repository is built through gated milestones. Generate code only for the approved current task.

## Always follow

- Read `project_control/current_milestone.yaml` before suggesting implementation work.
- Use `docs/04_TASK_SPECS.md` as the authoritative task contract.
- Respect `docs/02_GLOBAL_INVARIANTS.md` even if a local implementation seems simpler without them.
- Add deterministic construction tests for new behavior.
- Do not generate implementation for future milestones.
- Keep provider API clients, registry, graph, embeddings, ontology, and MCP as separate modules.

## Identity rule

Provider IDs are external identifiers. After canonical registry construction, every graph node, vector record, ontology claim, and MCP result must use `canonical_paper_id` as the internal paper reference.

## Persistence rule

Raw provider data is append-only. Persistent artifacts must carry `snapshot_id` and `schema_version` once these fields exist.

## MCP rule

MCP tools must be allowlisted, typed, read-only in base v1, and must not expose arbitrary backend query execution.

## Testing rule

Construction tests should be small, fixture-driven, and independent of real corpus size. Product evaluation gates may use larger snapshots or cloud resources, but they are separate from construction tests.

## Non-goal rule

If the current task says something is a non-goal, do not implement it. Add a TODO or ADR note instead.
