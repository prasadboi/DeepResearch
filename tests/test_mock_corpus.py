"""Construction test for the mock corpus fixture and its fake flow."""

from __future__ import annotations

import pytest

from litgraph.examples.mock_corpus import (
    MockCorpus,
    load_mock_corpus,
    summarize,
    verify_fake_flow,
)


def test_mock_corpus_validates() -> None:
    corpus = load_mock_corpus()

    # Fixture parses into validated schema objects.
    assert isinstance(corpus, MockCorpus)

    counts = summarize(corpus)
    assert counts["canonical_papers"] >= 2
    assert counts["citation_records"] >= 1
    assert counts["embedding_records"] >= 1
    assert counts["ontology_claims"] >= 1

    # The complete fake flow resolves end to end.
    verify_fake_flow(corpus)


def test_verify_fake_flow_detects_broken_reference() -> None:
    corpus = load_mock_corpus()
    corpus.embedding_records[0].canonical_paper_id = "does-not-exist"
    with pytest.raises(ValueError):
        verify_fake_flow(corpus)
