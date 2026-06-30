.PHONY: install test lint typecheck mock-corpus

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

typecheck:
	mypy litgraph

mock-corpus:
	python -m litgraph.examples.load_mock_corpus
