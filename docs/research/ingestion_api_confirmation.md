# Ingestion API confirmation memo (Task 1.1, Phase A)

**Status:** confirmed by human review. **Date:** 2026-06-29. **Sources:** official OpenAlex
(`developers.openalex.org`) and Semantic Scholar (`semanticscholar.org`, `api.semanticscholar.org`)
documentation only (see Sources at end), plus read-only live probes on 2026-06-29. Anything not
directly confirmed is listed under *Unknowns / risks*.

> ⚠️ Material change since older tutorials: OpenAlex **deprecated the "polite pool" `mailto`**
> (~Feb 2026) and moved to an **API-key + daily-budget freemium** model. Treat all $ figures and
> exact caps as provider-controlled and config-driven, not hard-coded.

## Provider 1 — OpenAlex

1. **Base URL:** `https://api.openalex.org`
2. **Authentication:** Optional but recommended. Freemium with a **daily usage budget**: a smaller
   free allowance with no key, a larger one with a free key (obtain at `openalex.org/settings/api`).
   Key is sent as a **query parameter `api_key=YOUR_KEY`**. Responses carry rate headers
   `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Credits-Used`, `X-RateLimit-Reset`.
3. **Paper search:** `GET /works?search=QUERY` (full-text). Structured search/filtering via
   `GET /works?filter=...` (e.g. `filter=title.search:...`, `filter=from_publication_date:...`).
4. **Paper lookup:** `GET /works/{openalex_id}` (e.g. `/works/W2741809807`). By DOI:
   `GET /works/https://doi.org/10.xxxx/...` **or** `GET /works?filter=doi:10.xxxx/...`. Bulk DOI via
   OR syntax `filter=doi:A|B|C`.
5. **References / citations:**
   - *Outgoing references:* each Work has **`referenced_works`** — an array of OpenAlex IDs it cites
     (`referenced_works_count` for the count).
   - *Incoming citations:* `GET /works?filter=cites:W123` returns citing works; **`cited_by_count`**
     gives the count; `cited_by_api_url` is a prebuilt link.
6. **Available raw fields (Work object):** `title` / `display_name`; **`abstract_inverted_index`**
   (abstract is an inverted index, not plain text — must be reconstructed downstream, not by the
   client); `authorships[]` (`author.id`, `author.display_name`, institutions); `publication_year`;
   venue via `primary_location.source.display_name` (+ legacy `host_venue`); `doi` / `ids.doi`;
   external IDs under `ids` (`openalex`, `mag`, `pmid`); arXiv via `ids`/`locations`; `cited_by_count`;
   `referenced_works`; open access via `open_access.is_oa` + `open_access.oa_url` and
   `primary_location.pdf_url`. `select=field1,field2` trims the payload.
7. **Pagination:** `page` + `per_page` (default 25; **max 200 — live-verified:** `per_page=201` →
   HTTP 400 "per-page parameter must be between 1 and 200"). Basic paging capped at **10,000**
   results; deeper paging via **cursor pagination `cursor=*` — live-verified** (response
   `meta.next_cursor` returned). (Live note: `meta.cost_usd` is now present per request, e.g.
   `0.0001` for a list+select — confirms the budget model.) *Doc/live discrepancy:* the paging guide
   says `per_page` 1–100; the live API accepts up to **200**.
7b. **Batch / bulk ingestion (OpenAlex):** no POST batch endpoint; instead **batch-by-id via the OR
   pipe filter** `GET /works?filter=openalex:W1|W2|...` (also `filter=doi:A|B|...`) — **live-verified**
   (2 ids → 2 results in one request). OR cap is ~50–100 values per filter (docs vary; chunk
   conservatively, config-driven). For very large pulls OpenAlex recommends the **data snapshot**,
   not deep cursor scraping.
8. **Rate limits:** daily budget enforced; burst cap (~100 req/s) → **429**; docs recommend
   **exponential backoff (`2^attempt` seconds)**. Per-op cost tiers (singleton retrieval free; list/
   filter cheap; search higher) — figures provider-controlled.
9. **Errors / status:** `200` success (lists return `meta` + `results`); `404` for unknown single
   entity; `4xx` for malformed queries; `429` over budget/burst.
10. **Tiny unauthenticated smoke check possible?** **Yes** — singleton retrieval works without a key
    and is free, e.g. `GET https://api.openalex.org/works/W2741809807`. Must stay optional/skipped by
    default per task invariants.

## Provider 2 — Semantic Scholar (Academic Graph API)

1. **Base URL:** `https://api.semanticscholar.org/graph/v1`
2. **Authentication:** Optional. Unauthenticated calls allowed but share a **global pool** (rate-
   limited, unreliable for sustained use). API key recommended, sent as HTTP header
   **`x-api-key: YOUR_KEY`** (requested on the S2 site, delivered by email). Introductory key limit
   ~**1 RPS** across endpoints.
3. **Paper search:** relevance — `GET /paper/search?query=...&offset=&limit=&fields=...`; bulk —
   `GET /paper/search/bulk?query=...&token=...&fields=...` with filters `year`, `venue`,
   `fieldsOfStudy`, `minCitationCount`, `openAccessPdf`, `publicationTypes`, `publicationDateOrYear`,
   `sort`.
4. **Paper lookup:** `GET /paper/{paper_id}?fields=...`; batch — `POST /paper/batch` (body
   `{"ids":[...]}` + `fields` query). **paper_id formats:** raw S2 hash
   (`649def34f8be52c8b66281af98ae884c09aef38b`), `DOI:10...`, `ARXIV:1234.5678`, `CorpusId:...`
   (also `PMID:`, `MAG:`, `ACL:`, `URL:`).
5. **References / citations:** `GET /paper/{paper_id}/references?fields=...&offset=&limit=` (papers
   this paper cites) and `GET /paper/{paper_id}/citations?fields=...&offset=&limit=` (papers citing
   it). `references`/`citations` can also be requested as fields on the detail call (capped subset);
   counts via `referenceCount` / `citationCount`.
6. **Available raw fields:** `title`, `abstract` (may be `null` due to licensing), `year`, `venue`,
   `publicationVenue`, `authors[]` (`authorId`, `name`), `externalIds` (`DOI`, `ArXiv`, `MAG`,
   `PubMed`, `CorpusId`, `ACL`, `DBLP`), `citationCount`, `referenceCount`, `references`, `citations`,
   `openAccessPdf` (`url`, `status`), `isOpenAccess`, `fieldsOfStudy`, `publicationTypes`,
   `publicationDate`, `url`. `fields` is comma-separated, no spaces.
7. **Pagination:** relevance search `offset`+`limit` (`limit` max ~100; **`offset+limit` must be
   `< 1000` — live-verified:** HTTP 400 "Relevance search offset + limit must be < 1000. Consider
   '/paper/search/bulk'..."); bulk search **`token`** continuation (~1000/page);
   `references`/`citations` `offset`+`limit` (`limit` max ~1000 — *not* live-verified, hit anon 429).
7b. **Batch / bulk ingestion (S2):** `POST /paper/batch` with body `{"ids":[...]}` (max **500** ids)
   + `?fields=...` — **live-verified** (2 ids → array with full `externalIds`, even unauthenticated on
   this probe). **`GET /paper/search/bulk`** uses **`token`** continuation (~1000/page, ~10M total)
   and escapes the relevance `offset+limit<1000` cap — preferred for large query-based pulls.
   `POST /author/batch` exists analogously.
8. **Rate limits:** **429** on exceed; anon shared pool; key ~1 RPS default. Mitigate with backoff +
   serialized (single-flight) requests.
9. **Errors / status:** `200` success; `400` malformed params; `401` invalid/missing auth (key-gated
   endpoints); `404` paper not found; `429` rate limited.
10. **Tiny unauthenticated smoke check possible?** **Yes** — e.g.
    `GET /paper/DOI:10.../?fields=title,year` without a key, but the shared pool may 429. Keep
    optional/skipped by default.

## Cross-cutting unknowns / risks

- **OpenAlex pricing/limits in flux** post-Feb-2026 (polite-pool removed); exact daily budget and
  per-op costs differ slightly across doc pages → keep all limits/keys in **config**, never hard-coded.
- **Caps resolved live (2026-06-29):** OpenAlex `per_page` **max 200** (docs say 100), `cursor=*`,
  and **OR-filter batch-by-id** all confirmed; S2 relevance **`offset+limit < 1000`** and
  **`POST /paper/batch`** both confirmed. **Still unverified:** S2 `references`/`citations` `limit` max
  (anon **429**) and the exact OpenAlex OR cap (50 vs 100) → confirm with a key / larger probe.
- **S2 anon pool confirmed flaky:** two unauthenticated calls returned **429** during verification;
  any live path must use a key and stay optional/skipped by default.
- **Abstract handling:** OpenAlex gives `abstract_inverted_index` (not plain text); S2 `abstract`
  may be `null`. Clients must return these **raw and unmodified** — reconstruction/normalization is a
  later stage (non-goal here).
- **arXiv id location** in OpenAlex schema (`ids` vs `locations`) varies — store raw, don't infer.
- **No identifier coupling:** provider IDs (OpenAlex `Wxxxx`, S2 hash, DOI, arXiv) are provider-
  scoped only; the client must not mint `canonical_paper_id` (enforced by Task 1.1 invariants/tests).

## Sources

- OpenAlex: <https://developers.openalex.org/> · API overview
  <https://developers.openalex.org/api-reference/introduction> · Authentication & pricing
  <https://developers.openalex.org/api-reference/authentication> · Works
  <https://developers.openalex.org/api-reference/works> · Page through results
  <https://developers.openalex.org/guides/page-through-results> · LLM quick reference
  <https://developers.openalex.org/guides/llm-quick-reference>
- Semantic Scholar: API product <https://www.semanticscholar.org/product/api> · Tutorial
  <https://www.semanticscholar.org/product/api/tutorial> · API docs
  <https://api.semanticscholar.org/api-docs/> · Public-API FAQ
  <https://www.semanticscholar.org/faq/public-api>
