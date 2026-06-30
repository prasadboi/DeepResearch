"""Mock-corpus command (Stage 0, Task 0.2).

Loads the synthetic mock corpus, validates every record against the core
schemas, and verifies the complete fake flow:

    raw record -> canonical paper -> citation -> embedding record -> ontology claim

The command is read-only: it writes nothing to disk, honoring the invariant
that no artifact is written outside configured artifact directories.

Run with::

    python -m litgraph.examples.load_mock_corpus
"""

from __future__ import annotations

from litgraph.config import load_config
from litgraph.examples.mock_corpus import load_mock_corpus, summarize, verify_fake_flow


def main() -> int:
    """Load and validate the mock corpus, print a summary, and exit."""
    config = load_config()
    corpus = load_mock_corpus()
    verify_fake_flow(corpus)

    print(f"[load_mock_corpus] environment={config.environment}")
    print(f"[load_mock_corpus] snapshot_id={corpus.snapshot_manifest.snapshot_id}")
    for name, count in summarize(corpus).items():
        print(f"[load_mock_corpus] {name}={count}")

    citation = corpus.citation_records[0]
    embedding = corpus.embedding_records[0]
    claim = corpus.ontology_claims[0]
    print(
        "[load_mock_corpus] fake flow OK: "
        f"raw({corpus.paper_records[0].provider_record_id}) -> "
        f"canonical({citation.source_canonical_paper_id}) -> "
        f"cites({citation.target_canonical_paper_id}) -> "
        f"embedding({embedding.embedding_id}) -> "
        f"claim({claim.claim_id})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
