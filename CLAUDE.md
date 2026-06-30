# Claude Code instructions for LitGraph

You are working on a milestone-gated proof of concept. Do not build ahead.

## Primary rule

Only implement the task explicitly named in `project_control/current_milestone.yaml` and the current user-approved task prompt. If a future component seems useful, add a TODO or ADR note. Do not implement it.

## Project boundary

LitGraph is a literature-review retrieval substrate exposed through MCP. It uses three offline-built structures:

1. Citation + metadata graph.
2. Vector embedding search table.
3. Ontology claim graph.

The MCP server is the agent-facing abstraction over these structures. The agent should not access graph databases, vector stores, raw provider APIs, or ontology tables directly.

## Coding behavior

Before editing code:

1. Read `project_control/current_milestone.yaml`.
2. Read `docs/02_GLOBAL_INVARIANTS.md`.
3. Read the matching task in `docs/04_TASK_SPECS.md`.
4. Confirm the task's non-goals.

While editing code:

- Keep changes minimal and stage-local.
- Add or update construction tests for every behavior added.
- Do not introduce new services, dependencies, or cloud resources unless the current task requires them.
- Do not add query-time ingestion.
- Do not create arbitrary database query tools.
- Do not log secrets, API keys, tokens, or raw credentials.
- Do not make external network calls inside unit tests.
- Do not couple graph, vector, or ontology identities to provider IDs. Use `canonical_paper_id` after the registry stage.
- Preserve append-only raw snapshots.
- Keep every persistent artifact tied to `snapshot_id` and `schema_version` once those schemas exist.

After editing code:

1. Run the construction tests listed for the task.
2. Run the stage evaluation command if the task has one and the required resources exist.
3. Update any affected docs or ADRs.
4. Summarize what changed, which tests passed, and which evaluation gate remains blocked if any.

## Stop conditions

Stop and ask for human direction when:

- The task requires a design choice not already answered in the task spec.
- A required provider, cloud service, model, or benchmark API is unavailable.
- The implementation would require building a future-stage component.
- The construction tests pass but the evaluation gate fails.
- The task seems to require changing a global invariant.

## Prohibited in base v1

- Query-time paper ingestion.
- Periodic model training.
- Agent write operations.
- Arbitrary Cypher, SQL, Python, shell, or provider API passthrough through MCP.
- Full frontend implementation.
- Full AstaBench optimization before the evaluation adapter and internal ablations exist.
