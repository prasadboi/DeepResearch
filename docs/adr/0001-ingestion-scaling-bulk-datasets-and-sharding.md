# ADR 1: Ingestion scaling — bulk datasets, sharding, and streaming

## Status

Proposed

## Context

The Stage 1 ingestion path (Tasks 1.1–1.2) fetches raw provider records through synchronous
`ProviderClient`s and persists them with `RawSnapshotStore.write_snapshot(...)`. This design is
correct and sufficient for the bounded proof-of-concept (a small, pre-ingested demo corpus), but it
is **not** built to ingest a very large corpus (hundreds of thousands to millions of papers). The
specific limits, all in the current code:

1. **In-memory accumulation.** Clients return `list[PaperRecord]`, and `write_snapshot` accepts the
   full `records_by_provider` mapping in memory and writes it in one pass. Millions of Pydantic
   objects (each carrying a full `raw_payload`) will not fit in RAM.
2. **Write-once, no incremental append or resume.** `write_snapshot` materializes everything, writes
   one file per provider, then checksums at the end. A run cannot stream, checkpoint, or resume;
   append-only-via-exclusive-create means a failed large run must be `--force`-restarted from zero.
3. **One unbounded JSONL per provider per snapshot.** `<provider>.jsonl` grows without bound; it
   cannot be sharded or parallelized, and `validate_snapshot` re-checksums the whole file (O(file)).
4. **Provider throughput and cost are the real ceiling.** Clients are intentionally synchronous
   single-flight. Semantic Scholar is ~1 req/s with a key; OpenAlex enforces a daily budget and now
   **charges per request**. Paginating millions of papers is days-to-weeks of serialized calls and a
   real monetary cost.
5. **No delta/incremental ingestion.** Every snapshot is a full pull; re-running re-fetches
   everything rather than only what changed.

What is already scale-friendly and should be preserved: `iter_records()` and `sha256_file()` stream
(chunked); snapshots are append-only/immutable with manifests + checksums; transport is injectable;
limits/batch sizes are config-driven; identity stays provider-scoped (no canonical IDs minted at
ingestion).

## Decision

Keep the current API-client + local-snapshot design for the PoC and for **targeted/incremental**
pulls (seed sets, a venue, recent papers). Do **not** scale it by crawling whole corpora through the
paginated API. When large-corpus ingestion is actually required, introduce — additively, behind the
existing interfaces — the following, rather than rewriting:

1. **Bulk-dataset ingestion path** alongside the API clients: OpenAlex **data snapshot** and Semantic
   Scholar **Datasets API** (both bulk, free, built for full-corpus pulls; OpenAlex explicitly
   recommends the snapshot over API crawling).
2. **Streaming fetch → streaming/append write** (iterators end-to-end) so memory is bounded.
3. **Sharded / partitioned snapshot files** (e.g. `<provider>/part-NNNNN.jsonl`) with per-shard
   manifests, enabling parallel fetch/write, partial validation, and resumability.
4. **Delta/incremental snapshots** (ingest only new/changed records since the last snapshot).

No code changes are made by this ADR; it records the boundary and the migration plan before code
depends on the assumption that the API path scales.

## Consequences

- **Improves:** sets explicit expectations (API clients = targeted/incremental; bulk datasets =
  whole-corpus), avoiding an accidental, slow, expensive full-corpus API crawl. Keeps the immutable,
  manifest-backed snapshot contract as the stable foundation that sharding/streaming extend.
- **Gets harder / must be respected by future tasks:** the snapshot directory layout and manifest
  schemas (`SnapshotManifest`, `IngestionManifest`) must evolve to allow multiple shard files per
  provider and per-shard checksums **without** breaking local↔cloud parity (Task 1.3) — i.e. the
  cloud uploader must treat a snapshot as a set of objects, not a single file per provider.
- **Out of scope for base v1 unless promoted:** async/concurrent fetching with rate-limit governance,
  a job scheduler/queue, and any query-time ingestion (still prohibited).

## Alternatives considered

- **Scale the API-crawl path (async + more workers).** Rejected for whole-corpus: provider rate
  limits and per-request cost cap throughput regardless of client concurrency; bulk datasets are the
  provider-sanctioned mechanism.
- **Stream provider responses straight into cloud storage (skip local).** Rejected: violates the
  local-first promotion model, append-only raw-snapshot invariant, and the local↔cloud parity check
  that depends on a local source of truth.
- **Rewrite the store now for sharding/streaming.** Rejected: premature for the PoC; would build
  ahead of an actual large-corpus requirement. The change is additive when needed.

## Follow-up tasks

- [ ] Before any large-corpus ingestion, write a follow-up ADR (or task spec) defining the sharded
      snapshot layout + per-shard manifests and the streaming/append writer API.
- [ ] In Task 1.3 (cloud raw storage), model a snapshot as a **set of objects** (keys include
      `snapshot_id`) so it already accommodates future multi-shard snapshots.
- [ ] Evaluate the OpenAlex data snapshot and Semantic Scholar Datasets API as a separate
      bulk-ingestion task when full-corpus coverage is required.
