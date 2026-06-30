# Global invariants

These rules apply to every task unless an ADR explicitly changes them.

## Product invariants

1. The base system uses a pre-ingested corpus.
2. Query-time ingestion is not allowed in base v1.
3. The MCP server is the agent-facing abstraction over graph, vector, and ontology layers.
4. The agent must receive provenance for returned papers, chunks, claims, and edges.
5. Human review is required before moving between milestone gates.

## Data invariants

1. Raw provider data is append-only.
2. Every persisted snapshot has `snapshot_id`.
3. Every persisted schema has `schema_version`.
4. Provider IDs are external identifiers, not internal primary keys.
5. After the registry stage, every layer references papers by `canonical_paper_id`.
6. One external record may map to only one canonical paper.
7. A canonical paper must have at least one external record.
8. No graph/vector/ontology layer may create its own independent paper identity namespace.

## Job invariants

1. Offline jobs must be idempotent for the same input and `snapshot_id`.
2. Jobs must write machine-readable reports.
3. Jobs must fail with typed errors when required inputs are missing.
4. Jobs must not silently drop invalid records. They must report rejection reasons.

## Testing invariants

1. Construction tests are deterministic and fixture-driven.
2. Construction tests must not depend on real corpus size.
3. Construction tests must not require live network calls.
4. Evaluation gates may use real snapshots, cloud resources, and benchmark subsets.
5. Evaluation failures block the next task even if construction tests pass.

## Security invariants

1. No secrets in committed config files.
2. Secrets must be injected through environment variables or secret manager.
3. Logs must redact credentials, API keys, tokens, and secret values.
4. MCP tools require authentication in non-local mode.
5. MCP tools are allowlisted.
6. No arbitrary Cypher, SQL, Python, shell, or provider API passthrough through MCP.
7. MCP tools are read-only in base v1.

## Observability invariants

1. Every long-running job logs `run_id`, `snapshot_id`, and `schema_version` where applicable.
2. Every MCP tool call logs `request_id`, tool name, input shape, result count, latency, and error type if failed.
3. Evaluation runs log configuration, corpus snapshot, agent/model configuration, metrics, and artifacts.
4. Logs must be sufficient to reproduce a product-level failure.

## Cloud invariants

1. Cloud loads use the same semantics as local loads.
2. Cloud and local artifacts must be comparable through parity reports.
3. Cloud resources must be created through documented config, not manual edits.
4. Destructive cloud operations require explicit confirmation and are not part of routine task execution.
