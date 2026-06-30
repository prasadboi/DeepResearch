# Task specifications

Each task is a bounded coding problem. Do not implement non-goals. Do not proceed to the next task until construction tests and the evaluation gate pass.

## Stage 0: Project scaffold

### Task 0.1: Repository layout and local runtime

#### Product goal

Create a repository that can support staged development without allowing later components to leak into earlier milestones.

#### Inputs

- Empty or existing repo

#### Outputs

- Package layout, config skeleton, local command placeholders, mock-corpus command placeholder

#### Non-goals

- No provider API calls
- No graph database population
- No embeddings
- No MCP server
- No ontology code beyond placeholder interfaces

#### Programming invariants

- All packages import cleanly
- All config is loaded through one config module
- No module reads environment variables directly except config.py
- No persistent artifact is written outside configured artifact directories

#### Construction tests

- `test_import_all_modules`
- `test_config_loads_from_fixture`
- `test_artifact_paths_are_under_project_root`

#### Evaluation gate

make test, make lint, make typecheck, and python -m litgraph.examples.load_mock_corpus must pass.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 0.2: Core schemas and mock data

#### Product goal

Define stable objects that later layers reference without implementing persistence or provider logic.

#### Inputs

- Mock corpus fixture

#### Outputs

- Schema classes for PaperRecord, ExternalRecord, CanonicalPaper, CitationRecord, EmbeddingRecord, OntologyClaim, OntologyEntity, OntologyEdge, EvidenceSpan, SnapshotManifest

#### Non-goals

- No real normalization
- No deduplication
- No database writes

#### Programming invariants

- Every schema has schema_version
- Every corpus object has snapshot_id
- Paper-like objects carry provider identifiers without using them as internal IDs

#### Construction tests

- `test_schema_roundtrip_json`
- `test_schema_rejects_missing_snapshot_id`
- `test_schema_rejects_invalid_provider_name`
- `test_mock_corpus_validates`

#### Evaluation gate

The mock corpus must support a complete fake flow from raw record to canonical paper to citation to embedding record to ontology claim.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 1: Raw paper ingestion and raw cloud storage

### Task 1.1: Provider client interfaces

#### Product goal

Create provider clients that fetch raw records behind a common interface.

#### Inputs

- Provider config
- Mock provider responses

#### Outputs

- OpenAlexClient
- SemanticScholarClient
- ProviderClient interface

#### Non-goals

- No deduplication
- No graph construction
- No embeddings
- No ontology extraction
- No cloud upload yet

#### Programming invariants

- Provider clients return raw payloads plus fetch metadata
- Provider clients do not create canonical IDs
- Provider clients do not mutate payload fields
- Provider failures return typed errors
- Retry and rate-limit behavior is explicit

#### Construction tests

- `test_openalex_client_parses_mock_response`
- `test_semantic_scholar_client_parses_mock_response`
- `test_provider_error_is_typed`
- `test_provider_client_does_not_create_canonical_ids`

#### Evaluation gate

A tiny smoke ingestion must fetch raw records, record provider name and fetch timestamp, and create no canonical IDs.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 1.2: Raw snapshot store and manifest

#### Product goal

Store raw provider data in immutable snapshot form.

#### Inputs

- Raw provider records

#### Outputs

- Raw JSONL files
- SnapshotManifest
- IngestionManifest

#### Non-goals

- No canonical registry
- No graph
- No vector index

#### Programming invariants

- Raw snapshots are append-only
- Same snapshot_id cannot be overwritten without explicit force flag
- Every raw file has a manifest
- Every manifest records provider, query/config, created_at, record_count, and checksum

#### Construction tests

- `test_raw_store_writes_jsonl`
- `test_raw_store_refuses_overwrite_without_force`
- `test_manifest_contains_checksum`
- `test_manifest_record_count_matches_file`

#### Evaluation gate

Running ingestion for the demo corpus must create a snapshot directory, provider JSONL files, manifests, and valid checksums.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 1.3: Cloud raw storage

#### Product goal

Upload raw snapshots to cloud storage without changing the local snapshot format.

#### Inputs

- Local raw snapshot

#### Outputs

- Cloud snapshot objects
- Cloud manifest

#### Non-goals

- No cloud graph
- No cloud vector DB
- No MCP cloud deployment

#### Programming invariants

- Cloud object keys include snapshot_id
- Cloud upload is idempotent
- Cloud and local manifests have matching checksums
- Secrets are never written to logs

#### Construction tests

- `test_cloud_key_includes_snapshot_id`
- `test_upload_plan_is_deterministic`
- `test_secret_values_are_redacted_from_logs`

#### Evaluation gate

Uploading one demo snapshot must produce cloud manifests with matching checksums and rerun without duplicated artifacts.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 2: Canonical paper registry

### Task 2.1: Normalization

#### Product goal

Map raw provider records into normalized paper candidates.

#### Inputs

- Raw snapshot

#### Outputs

- Normalized paper candidates
- Typed rejection report

#### Non-goals

- No deduplication
- No graph construction
- No embeddings

#### Programming invariants

- Normalization is deterministic
- Provider fields are preserved in ExternalRecord
- Missing optional fields do not crash normalization
- Title normalization is stable
- DOI/arXiv/S2/OpenAlex IDs are identifiers, not primary keys

#### Construction tests

- `test_normalize_openalex_fixture`
- `test_normalize_semantic_scholar_fixture`
- `test_missing_abstract_allowed`
- `test_title_normalization_deterministic`

#### Evaluation gate

Every raw record becomes a normalized candidate or a typed rejection; report raw count, normalized count, rejection count, and missing metadata rates.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 2.2: Deduplication and canonical IDs

#### Product goal

Merge provider records that refer to the same paper.

#### Inputs

- Normalized candidates

#### Outputs

- Canonical paper registry
- ExternalRecord mappings
- Merge report

#### Non-goals

- No citation graph
- No vector index
- No ontology

#### Programming invariants

- Canonical IDs are stable for the same normalized input
- Exact DOI matches merge
- Exact arXiv ID matches merge
- Provider-paper ID matches only within provider namespace
- Title fuzzy matching cannot merge without year or venue support
- All merged records remain traceable

#### Construction tests

- `test_exact_doi_merge`
- `test_exact_arxiv_merge`
- `test_same_title_different_year_does_not_merge`
- `test_external_records_preserved_after_merge`
- `test_canonical_id_stable`

#### Evaluation gate

Registry build must create canonical papers, a duplicate merge report, no paper with zero external records, and no ExternalRecord pointing to multiple canonical papers.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 2.3: Registry report

#### Product goal

Expose corpus quality before graph construction.

#### Inputs

- Canonical registry

#### Outputs

- registry_report.md
- registry_report.json

#### Non-goals

- No mutation of registry
- No graph construction

#### Programming invariants

- Report generation is read-only
- Report includes snapshot_id
- Report can run on any valid registry snapshot

#### Construction tests

- `test_registry_report_contains_required_sections`
- `test_registry_report_is_read_only`

#### Evaluation gate

Report must include raw records by provider, canonical paper count, duplicate merge count, missing DOI/abstract rates, year distribution, venue distribution, and top cited papers if available.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 3: Citation + metadata graph

### Task 3.1: Graph schema and migrations

#### Product goal

Create a versioned graph schema for citation and metadata graph storage.

#### Inputs

- Canonical registry schema

#### Outputs

- Graph migration files
- Constraints
- Indexes
- schema_version record

#### Non-goals

- No data load
- No embeddings
- No MCP

#### Programming invariants

- Graph schema is versioned
- All Paper nodes use canonical_paper_id
- Provider IDs are ExternalRecord/identifier properties
- Migration order is deterministic

#### Construction tests

- `test_graph_schema_contains_required_constraints`
- `test_graph_schema_rejects_duplicate_canonical_paper_id`
- `test_migration_order_is_deterministic`

#### Evaluation gate

Applying migrations to empty local graph must create constraints, indexes, and record schema_version.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 3.2: Graph materializer

#### Product goal

Materialize canonical papers, authors, venues, external records, and citations into the local graph.

#### Inputs

- Canonical registry

#### Outputs

- Local graph data
- Unresolved citation report

#### Non-goals

- No cloud load
- No MCP
- No embeddings

#### Programming invariants

- Materialization is idempotent
- Unresolved citations are not silently dropped
- All edges reference canonical IDs or typed unresolved references
- No duplicate citation edges on rerun

#### Construction tests

- `test_materialize_paper_node_from_fixture`
- `test_materialize_author_node_from_fixture`
- `test_materialize_citation_edge_idempotent`
- `test_unresolved_citation_recorded`

#### Evaluation gate

Local graph node counts must match registry mapping rules, citation edge count must be nonzero when citations exist, and rerun must change zero records.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 3.3: Graph diagnostics

#### Product goal

Detect graph quality problems before cloud hosting.

#### Inputs

- Local graph

#### Outputs

- graph_diagnostics.md
- graph_diagnostics.json

#### Non-goals

- No graph mutation
- No cloud deployment

#### Programming invariants

- Diagnostics are read-only
- Diagnostics output JSON and Markdown

#### Construction tests

- `test_graph_diagnostics_read_only`
- `test_graph_diagnostics_reports_required_metrics`

#### Evaluation gate

Diagnostics must report paper/author/venue counts, citation edge count, unresolved citations, orphan papers, duplicate external identifiers, and largest connected components.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 4: Hosted rudimentary graph

### Task 4.1: Cloud graph deployment

#### Product goal

Deploy the graph schema to a cloud environment with no manual schema edits.

#### Inputs

- Graph migrations
- Cloud config

#### Outputs

- Cloud graph schema

#### Non-goals

- No data load until schema passes
- No MCP deployment

#### Programming invariants

- Cloud graph is created from migrations
- Secrets use environment or secret manager only
- No manual schema edits required

#### Construction tests

- `test_cloud_config_schema_validates`
- `test_no_secret_values_in_config_files`
- `test_migration_plan_serializes`

#### Evaluation gate

Cloud graph schema_version, constraint names, and index names must exactly match local schema.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 4.2: Cloud graph load

#### Product goal

Load the citation graph to cloud and verify local-cloud parity.

#### Inputs

- Local graph data
- Cloud graph schema

#### Outputs

- Cloud graph data
- parity report

#### Non-goals

- No vector search
- No ontology
- No MCP write tools

#### Programming invariants

- Cloud load uses same materializer semantics as local
- Cloud graph records snapshot_id
- Local and cloud counts are comparable

#### Construction tests

- `test_cloud_loader_uses_snapshot_id`
- `test_cloud_loader_refuses_unknown_schema_version`

#### Evaluation gate

Parity report must show exact matching paper count, citation edge count, and author count; 10 sampled paper neighborhood queries must return the same canonical paper IDs locally and in cloud.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 5: Secure MCP graph server

### Task 5.1: MCP server skeleton

#### Product goal

Expose read-only graph operations through typed MCP tools.

#### Inputs

- Hosted/local graph

#### Outputs

- MCP server skeleton
- get_paper
- expand_citations
- get_paper_neighborhood

#### Non-goals

- No vector search tools
- No ontology tools
- No arbitrary DB query tool

#### Programming invariants

- MCP tools have typed input/output schemas
- Every response includes request_id and snapshot_id
- Unknown tools fail safely

#### Construction tests

- `test_mcp_tool_schema_validates`
- `test_mcp_rejects_unknown_tool`
- `test_mcp_response_contains_request_id`

#### Evaluation gate

Scripted MCP smoke test must show get_paper, expand_citations, get_paper_neighborhood work and invalid tools fail safely.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 5.2: MCP auth, logging, and allowlist

#### Product goal

Secure MCP before connecting an agent.

#### Inputs

- MCP skeleton

#### Outputs

- Auth enforcement
- Tool-call logging
- Allowlist config

#### Non-goals

- No agent workflow optimization
- No write tools

#### Programming invariants

- All tools require authentication in non-local mode
- Unauthorized requests fail closed
- Every tool call is logged
- Logs redact secrets and user credentials

#### Construction tests

- `test_unauthenticated_request_rejected`
- `test_authorized_request_allowed`
- `test_tool_call_logged`
- `test_logs_redact_secrets`

#### Evaluation gate

Security eval must reject 100% unauthorized scripted calls, allow 100% authorized scripted calls, and show no secret values in logs.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 6: Embedding and RAG pipeline

### Task 6.1: Chunking and embedding records

#### Product goal

Create stable chunks and embedding records from canonical papers.

#### Inputs

- Canonical registry
- Text fields

#### Outputs

- Chunk records
- EmbeddingRecord schema
- embedding build report

#### Non-goals

- No query-time embeddings
- No MCP search tools yet
- No ontology

#### Programming invariants

- Chunk IDs are stable for same text/config
- Embedding records reference canonical_paper_id
- Embedding records include model metadata and dimensions
- No embeddings generated at query time in v1

#### Construction tests

- `test_chunk_ids_stable`
- `test_chunk_offsets_valid`
- `test_embedding_record_requires_model_metadata`
- `test_embedding_record_references_canonical_paper`

#### Evaluation gate

Embedding build on demo snapshot must create at least one paper-level embedding for every searchable paper with title or abstract text; papers without searchable text must be listed with typed missing-text reasons.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 6.2: Vector search

#### Product goal

Support local vector search over precomputed embeddings with filters and provenance.

#### Inputs

- Embedding records
- Canonical registry

#### Outputs

- Vector index
- search API

#### Non-goals

- No cloud vector index
- No MCP search update yet

#### Programming invariants

- Search returns canonical_paper_id
- Search results include score and provenance
- Filters are deterministic
- Search is read-only

#### Construction tests

- `test_vector_search_returns_canonical_ids`
- `test_filter_by_year`
- `test_filter_by_venue`
- `test_search_is_read_only`

#### Evaluation gate

Internal retrieval eval must show embedding search Recall@20 >= metadata-only Recall@20 + 0.01 on the curated eval set, filter correctness is 100%, and duplicate canonical ID rate is 0.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 6.3: Search-then-expand locally

#### Product goal

Combine vector seed search with citation graph expansion.

#### Inputs

- Vector search
- Citation graph

#### Outputs

- local search_then_expand service
- ablation report

#### Non-goals

- No cloud deployment
- No ontology expansion

#### Programming invariants

- Seed and expanded results are distinguishable
- Every expanded paper records expansion reason
- Expansion depth is bounded
- No duplicate canonical IDs

#### Construction tests

- `test_search_then_expand_marks_seed_vs_expanded`
- `test_expansion_depth_limit_enforced`
- `test_no_duplicate_papers_in_result_set`

#### Evaluation gate

Ablation eval must compare embedding only, citation expansion only, and embedding + citation expansion; combined mode Recall@20 must be >= embedding-only Recall@20, and filter correctness must remain 100%.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 7: Hosted RAG search

### Task 7.1: Cloud vector index

#### Product goal

Deploy precomputed embeddings to cloud vector storage.

#### Inputs

- Local embedding records

#### Outputs

- Cloud vector index
- vector index manifest

#### Non-goals

- No ontology
- No MCP ontology

#### Programming invariants

- Cloud vector records include snapshot_id
- Cloud index records embedding model metadata
- Cloud index load is idempotent
- Dimension mismatch is rejected

#### Construction tests

- `test_vector_index_manifest_validates`
- `test_cloud_vector_load_plan_deterministic`
- `test_vector_index_refuses_dimension_mismatch`

#### Evaluation gate

Cloud vector search parity must show Jaccard@20 >= 0.80 against local top-20 results for each scripted query, 100% canonical IDs, and 100% provenance coverage.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 7.2: Hosted hybrid search API

#### Product goal

Expose hosted vector search with filters and timing metadata.

#### Inputs

- Cloud vector index
- Cloud graph

#### Outputs

- Hosted hybrid search API

#### Non-goals

- No MCP update yet
- No ontology

#### Programming invariants

- top_k is bounded
- Filters are validated before execution
- Responses include timing metadata

#### Construction tests

- `test_top_k_limit_enforced`
- `test_invalid_filter_rejected`
- `test_response_contains_timing_metadata`

#### Evaluation gate

Hosted search eval must have Recall@20 >= local Recall@20 - 0.02, p95 latency <= 5 seconds on the scripted eval set, and 100% filter correctness on scripted cases.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 8: MCP search update

### Task 8.1: MCP search tools

#### Product goal

Expose hybrid search, chunk retrieval, and search-then-expand through MCP.

#### Inputs

- Secure MCP graph server
- Hosted hybrid search

#### Outputs

- hybrid_search
- get_relevant_chunks
- search_then_expand

#### Non-goals

- No ontology tools
- No backend internals exposed

#### Programming invariants

- Search tools do not expose vector DB internals
- Every returned paper has canonical_paper_id
- Every returned chunk has chunk_id and canonical_paper_id
- Every result has provenance

#### Construction tests

- `test_hybrid_search_tool_schema`
- `test_get_relevant_chunks_tool_schema`
- `test_search_then_expand_tool_schema`
- `test_mcp_search_rejects_invalid_filters`

#### Evaluation gate

Scripted agent/tool eval must call search_then_expand successfully, return seed/expansion provenance, reject invalid filters, and expose no arbitrary backend query.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 8.2: First AstaBench smoke adapter

#### Product goal

Prove the system can be wrapped for future AstaBench literature-understanding evaluation.

#### Inputs

- MCP search tools

#### Outputs

- AstaBench adapter skeleton
- eval traces

#### Non-goals

- No leaderboard claim
- No full benchmark run
- No ontology evaluation yet

#### Programming invariants

- Adapter calls MCP tools only
- Adapter logs run_id, snapshot_id, tools used, and returned paper IDs

#### Construction tests

- `test_astabench_adapter_uses_mcp_client`
- `test_eval_trace_contains_snapshot_id`
- `test_eval_trace_contains_tool_calls`

#### Evaluation gate

One or a few smoke examples must execute end-to-end, create logs, return paper IDs/provenance, and fail with typed errors when blocked.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 9: Ontology training and inference pipeline

### Task 9.1: Dataset adapters

#### Product goal

Convert AcademicGraph, SciERC, SciER, and optional SciNLP into canonical ontology JSONL.

#### Inputs

- Source IE datasets

#### Outputs

- canonical ontology JSONL
- dataset mapping report

#### Non-goals

- No target-corpus inference
- No graph materialization

#### Programming invariants

- Adapters preserve original labels
- Adapters emit canonical labels
- Every relation references valid entity IDs
- Every entity span has valid offsets
- Mapping confidence is recorded

#### Construction tests

- `test_academicgraph_adapter_fixture`
- `test_scierc_adapter_fixture`
- `test_scier_adapter_fixture`
- `test_relation_references_valid_entities`
- `test_entity_offsets_valid`

#### Evaluation gate

Dataset build report must show valid JSONL, no invalid offsets, no dangling relations, label distribution, and mapping-confidence distribution.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 9.2: One-time model training scaffold

#### Product goal

Train or run the ontology extractor manually, not periodically.

#### Inputs

- Canonical ontology JSONL

#### Outputs

- Training script
- Model artifact manifest
- Evaluation report

#### Non-goals

- No periodic training
- No automatic retraining job
- No MCP ontology tools

#### Programming invariants

- Training runs are versioned
- Model artifacts record dataset snapshot IDs
- Training config is saved with the artifact
- Model version is required for inference

#### Construction tests

- `test_training_config_serializes`
- `test_model_artifact_requires_version`
- `test_training_run_manifest_created`

#### Evaluation gate

Training/eval report must include entity metrics, relation metrics, confusion matrix, dataset breakdown, model_version, and must beat trivial baselines for entities and relations.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 9.3: Claim inference

#### Product goal

Run ontology inference over target corpus and create evidence-backed Claims.

#### Inputs

- Canonical papers
- Chunks
- Model artifact

#### Outputs

- Claim records
- Claim quality report

#### Non-goals

- Claims do not directly become final ontology edges
- No MCP ontology tools

#### Programming invariants

- Claims reference canonical_paper_id
- Claims reference chunk_id or source text location
- Claims include subject, predicate, object, evidence span, confidence, and model_version
- Low-confidence filtering is explicit

#### Construction tests

- `test_claim_requires_evidence_span`
- `test_claim_requires_model_version`
- `test_claim_references_canonical_paper`
- `test_low_confidence_claim_filtering`

#### Evaluation gate

Claim audit must show 0 schema-invalid claims, 100% claims with evidence spans, non-degenerate confidence distribution, and sampled human-audit precision >= 0.70 on at least 30 randomly sampled claims or all claims if fewer than 30 exist.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 9.4: Ontology edge materialization

#### Product goal

Aggregate Claims into materialized ontology edges.

#### Inputs

- Claim records

#### Outputs

- OntologyEntity records
- OntologyEdge records
- edge diagnostics

#### Non-goals

- No cloud ontology load
- No MCP ontology tools

#### Programming invariants

- Every ontology edge has at least one supporting claim
- Edges store supporting_claim_ids
- Edges store supporting_paper_count, mean_confidence, max_confidence
- Duplicate claim support is not double-counted

#### Construction tests

- `test_edge_requires_supporting_claim`
- `test_duplicate_claim_not_double_counted`
- `test_edge_aggregation_metrics_correct`

#### Evaluation gate

Ontology diagnostics must show 0 unsupported edges, 0 schema-invalid edges, median materialized ontology edges per paper <= 50 for the demo corpus unless overridden by ADR, and 100% evidence-backed sampled explanations over at least 20 sampled edges or all edges if fewer than 20 exist.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 10: Hosted ontology graph

### Task 10.1: Cloud ontology storage

#### Product goal

Host ontology claims and edges in cloud alongside existing graph/search system.

#### Inputs

- Local ontology claims/edges
- Cloud graph/search environment

#### Outputs

- Cloud ontology storage
- parity report

#### Non-goals

- No MCP ontology update yet
- No retraining

#### Programming invariants

- Cloud ontology uses same canonical_paper_id as registry
- Ontology storage records model_version and snapshot_id
- Cloud load is idempotent

#### Construction tests

- `test_ontology_cloud_load_plan`
- `test_ontology_refuses_unknown_paper_id`
- `test_ontology_refuses_missing_model_version`

#### Evaluation gate

Cloud ontology parity must show exact matching local/cloud claim counts and edge counts; 10 sampled edge explanations must match by supporting claim IDs.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 11: MCP ontology update

### Task 11.1: Ontology MCP tools

#### Product goal

Expose ontology search and explanation without leaking storage internals.

#### Inputs

- Cloud ontology storage
- MCP server

#### Outputs

- get_claims_for_paper
- get_ontology_edges_for_paper
- expand_by_ontology
- explain_ontology_edge

#### Non-goals

- No ontology write tools
- No arbitrary ontology query

#### Programming invariants

- Every ontology edge returned through MCP has evidence
- Every explanation includes supporting claims
- Every claim includes paper/chunk provenance
- No ontology write tools in v1

#### Construction tests

- `test_get_claims_for_paper_schema`
- `test_explain_edge_requires_existing_edge`
- `test_expand_by_ontology_depth_limit`
- `test_no_ontology_write_tools_registered`

#### Evaluation gate

Scripted ontology MCP eval must return evidence-backed claims, explanations with supporting evidence, relation/depth-bounded ontology expansion, and no unsupported edges.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

## Stage 12: Base product and benchmark hardening

### Task 12.1: End-to-end literature-review workflow

#### Product goal

Support query + filters -> seed search -> citation expansion -> ontology expansion -> chunk retrieval -> ranked paper set with provenance.

#### Inputs

- MCP graph/search/ontology tools

#### Outputs

- literature-review workflow service
- internal ablation report

#### Non-goals

- No query-time ingestion
- No frontend
- No write operations

#### Programming invariants

- Every result has canonical_paper_id
- Every result records why it was retrieved
- Every result records which layer returned it
- Unavailable filters return typed explanations

#### Construction tests

- `test_literature_review_request_schema`
- `test_no_query_time_ingestion_called`
- `test_result_contains_retrieval_reason`
- `test_unavailable_filter_returns_typed_message`

#### Evaluation gate

Internal eval must compare embeddings only, citation graph only, embeddings + citation graph, and full layered system; full system Recall@20 must be >= embedding-only Recall@20 on the curated eval set, with 100% provenance coverage and 100% filter correctness.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.

### Task 12.2: AstaBench literature-understanding comparison

#### Product goal

Run agent + MCP system against relevant AstaBench literature-understanding tasks.

#### Inputs

- AstaBench adapter
- MCP tools
- Evaluation traces

#### Outputs

- benchmark logs
- ablation table
- cost/latency report

#### Non-goals

- No claim of solving all AstaBench categories
- No optimization for code/data-analysis/end-to-end discovery tasks in base v1

#### Programming invariants

- Runs log snapshot_id
- Runs log MCP tool calls
- Runs log model/agent configuration
- Runs are reproducible from config

#### Construction tests

- `test_astabench_config_validates`
- `test_astabench_run_logs_snapshot_id`
- `test_astabench_run_logs_tool_calls`

#### Evaluation gate

At least one selected literature-understanding benchmark subset must complete end-to-end; 100% of runs must log snapshot_id, agent/model config, MCP tool calls, cost if available, and latency; an ablation table must compare baseline agent, embeddings only, embeddings + citation graph, and full layered system.

#### Human checkpoint

Record pass/fail status, defects, accepted risks, and the next authorized task in `project_control/current_milestone.yaml`.
