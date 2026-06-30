# Milestone gates

Each milestone ends with a human review. The next milestone is not authorized until the current milestone's construction tests and evaluation gate pass.

| Stage | Name | Product outcome | Next authorized work |
|---:|---|---|---|
| 0 | Project scaffold | Repository structure, config, schemas, fixtures, test commands. | Raw ingestion. |
| 1 | Raw paper ingestion and raw cloud storage | Raw provider snapshots and manifests exist locally and in cloud. | Canonical registry. |
| 2 | Canonical paper registry | Raw records are normalized and deduplicated into stable canonical papers. | Citation graph. |
| 3 | Citation + metadata graph | Local graph supports paper, author, venue, external record, and citation queries. | Hosted graph. |
| 4 | Hosted rudimentary graph | Cloud graph has schema/data parity with local graph. | MCP graph server. |
| 5 | Secure MCP graph server | Read-only graph operations are available through authenticated MCP tools. | Embeddings/RAG. |
| 6 | Embedding and RAG pipeline | Offline embeddings and local vector search support high-quality seed retrieval. | Hosted RAG search. |
| 7 | Hosted RAG search | Cloud vector search/hybrid search matches local behavior. | MCP search update. |
| 8 | MCP search update | Agent can search, fetch chunks, and search-then-expand through MCP. | Ontology pipeline. |
| 9 | Ontology training and inference pipeline | Claims and ontology edges are generated from evidence-backed supervised extraction. | Hosted ontology graph. |
| 10 | Hosted ontology graph | Ontology claims and edges are hosted with local-cloud parity. | MCP ontology update. |
| 11 | MCP ontology update | Ontology expansion and explanations are exposed through MCP. | Base product hardening. |
| 12 | Base product and benchmark hardening | End-to-end literature-review substrate, internal ablations, and AstaBench comparison path. | Product iteration. |

## Gate rule

At each gate, record:

```text
what was built
construction tests passed
product evaluation results
known defects
accepted risks
human decision
next authorized task
```

Use the ADR system when a gate changes product scope, data contracts, cloud choices, model-training strategy, or MCP tool surface.
