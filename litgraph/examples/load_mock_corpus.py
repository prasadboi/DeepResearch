"""Mock-corpus command placeholder (Stage 0, Task 0.1).

Task 0.1 only wires this command into the local runtime and proves that
configuration and artifact paths resolve correctly. It loads no corpus: real
schema classes and mock data arrive in Task 0.2. The command writes nothing to
disk, so it trivially honors the invariant that no artifact is written outside
configured artifact directories.

Run with::

    python -m litgraph.examples.load_mock_corpus
"""

from __future__ import annotations

from litgraph.config import load_config


def main() -> int:
    """Print resolved runtime paths and exit successfully."""
    config = load_config()
    print(f"[load_mock_corpus] environment={config.environment}")
    print(f"[load_mock_corpus] project_root={config.project_root}")
    print(f"[load_mock_corpus] artifacts_dir={config.artifacts_dir}")
    print(
        "[load_mock_corpus] placeholder: no corpus loaded "
        "(schemas and mock data arrive in Task 0.2)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
