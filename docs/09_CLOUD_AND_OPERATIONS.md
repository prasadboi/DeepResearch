# Cloud and operations

## Promotion model

Each data layer is built locally first, then promoted to cloud.

```text
raw snapshots -> cloud object storage
citation graph -> cloud graph
embeddings -> cloud vector index
ontology claims/edges -> cloud ontology storage
```

## Cloud artifact requirements

Every cloud artifact must record:

```text
snapshot_id
schema_version
created_at
producer job
source manifest checksum where applicable
```

## Idempotency

Cloud upload/load jobs must be idempotent. Re-running the same job for the same `snapshot_id` should not duplicate records.

## Parity reports

Every cloud stage needs a parity report:

```text
local counts
cloud counts
sample query comparison
schema_version comparison
known differences
```

## Rollback and recovery

Base v1 should prefer immutable new snapshots over destructive updates.

Recovery strategy:

1. Keep previous snapshot intact.
2. Promote new snapshot alongside old snapshot.
3. Switch active snapshot only after parity and evaluation pass.
4. Revert active snapshot pointer if evaluation fails.

## Secrets

Secrets must not be stored in repository files. Use environment variables or a secret manager. Logs must redact secrets.

## Observability

Long-running jobs must log:

```text
run_id
snapshot_id
input manifests
output manifests
record counts
errors by type
start/end time
```

MCP service must log:

```text
request_id
tool name
input shape, not raw secrets
result count
latency
error type
snapshot_id
```
