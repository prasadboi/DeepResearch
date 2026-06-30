"""Single configuration entry point for LitGraph.

This is the **only** module permitted to read environment variables. Every
other module must obtain configuration by calling :func:`load_config` and
reading the returned :class:`Config`. This keeps env access centralized
(global invariant: "No module reads environment variables directly except
config.py") and makes configuration deterministic and testable.

All persistent artifacts must live under the configured ``artifacts_dir``,
which is validated to resolve under the project root. No real persistence is
implemented at this stage; only the path contract is established.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

#: Repository root (one level above the ``litgraph`` package directory).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Prefix for environment variables read by this module.
ENV_PREFIX = "LITGRAPH_"

#: Default name of the artifacts directory under the project root.
DEFAULT_ARTIFACTS_DIRNAME = "artifacts"

#: Default environment label.
DEFAULT_ENVIRONMENT = "local"


@dataclass(frozen=True)
class Config:
    """Resolved LitGraph configuration.

    Artifact subdirectories model the staged layout as *paths only*; no
    stage-specific code exists yet. All artifact paths are required to resolve
    under :attr:`project_root` (enforced by :meth:`validate`).
    """

    project_root: Path
    artifacts_dir: Path
    environment: str = DEFAULT_ENVIRONMENT

    @property
    def raw_dir(self) -> Path:
        return self.artifacts_dir / "raw"

    @property
    def registry_dir(self) -> Path:
        return self.artifacts_dir / "registry"

    @property
    def graph_dir(self) -> Path:
        return self.artifacts_dir / "graph"

    @property
    def vector_dir(self) -> Path:
        return self.artifacts_dir / "vector"

    @property
    def ontology_dir(self) -> Path:
        return self.artifacts_dir / "ontology"

    @property
    def reports_dir(self) -> Path:
        return self.artifacts_dir / "reports"

    def artifact_dirs(self) -> tuple[Path, ...]:
        """Return all configured artifact directories."""
        return (
            self.artifacts_dir,
            self.raw_dir,
            self.registry_dir,
            self.graph_dir,
            self.vector_dir,
            self.ontology_dir,
            self.reports_dir,
        )

    def validate(self) -> None:
        """Validate invariants; raise ``ValueError`` on violation.

        Ensures every artifact directory resolves under the project root so no
        persistent artifact can be written outside configured locations.
        """
        for path in self.artifact_dirs():
            resolved = path if path.is_absolute() else self.project_root / path
            if not resolved.resolve().is_relative_to(self.project_root):
                raise ValueError(
                    f"artifact path {resolved} is not under project root "
                    f"{self.project_root}"
                )


def _resolve_artifacts_dir(raw_value: str | None, project_root: Path) -> Path:
    """Resolve an artifacts-dir value (relative paths are rooted at project root)."""
    if raw_value is None:
        return project_root / DEFAULT_ARTIFACTS_DIRNAME
    candidate = Path(raw_value)
    return candidate if candidate.is_absolute() else project_root / candidate


def load_config(
    config_path: Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> Config:
    """Load configuration from an optional TOML file and the environment.

    Precedence for each setting: TOML file value -> ``LITGRAPH_*`` env var ->
    default. The ``env`` mapping defaults to ``os.environ``; tests inject a
    fake mapping for determinism. This call site is the only place the codebase
    reads ``os.environ``.

    Args:
        config_path: Optional path to a TOML config file.
        env: Environment mapping; defaults to ``os.environ``.

    Returns:
        A validated :class:`Config`.
    """
    env = os.environ if env is None else env

    file_data: dict[str, object] = {}
    if config_path is not None:
        file_data = tomllib.loads(Path(config_path).read_text(encoding="utf-8"))

    environment = (
        _as_str(file_data.get("environment"))
        or env.get(f"{ENV_PREFIX}ENVIRONMENT")
        or DEFAULT_ENVIRONMENT
    )
    artifacts_value = (
        _as_str(file_data.get("artifacts_dir"))
        or env.get(f"{ENV_PREFIX}ARTIFACTS_DIR")
    )

    config = Config(
        project_root=PROJECT_ROOT,
        artifacts_dir=_resolve_artifacts_dir(artifacts_value, PROJECT_ROOT),
        environment=environment,
    )
    config.validate()
    return config


def _as_str(value: object | None) -> str | None:
    """Coerce a TOML scalar to ``str`` or ``None`` if absent."""
    if value is None:
        return None
    return str(value)
