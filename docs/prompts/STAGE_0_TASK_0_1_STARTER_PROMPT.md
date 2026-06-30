# Starter prompt: Stage 0 Task 0.1

```text
You are implementing Stage 0 Task 0.1: Repository layout and local runtime.

Product goal:
  Create a repository that can support staged development without allowing later components to leak into earlier milestones.

Inputs:
  Empty or existing repo.

Outputs:
  - Package layout.
  - Config skeleton.
  - Local command placeholders.
  - Mock-corpus command placeholder.

Explicit non-goals:
  - No provider API calls.
  - No graph database population.
  - No embeddings.
  - No MCP server.
  - No ontology code beyond placeholder interfaces.

Programming invariants:
  - All packages import cleanly.
  - All config is loaded through one config module.
  - No module reads environment variables directly except config.py.
  - No persistent artifact is written outside configured artifact directories.

Construction tests required:
  - test_import_all_modules
  - test_config_loads_from_fixture
  - test_artifact_paths_are_under_project_root

Evaluation gate:
  make test, make lint, make typecheck, and python -m litgraph.examples.load_mock_corpus must pass.

Do not implement future-stage components. Add placeholders only where needed to keep imports clean.
```
