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
from dataclasses import dataclass, field
from pathlib import Path

#: Repository root (one level above the ``litgraph`` package directory).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

#: Prefix for environment variables read by this module.
ENV_PREFIX = "LITGRAPH_"

#: Default name of the artifacts directory under the project root.
DEFAULT_ARTIFACTS_DIRNAME = "artifacts"

#: Default environment label.
DEFAULT_ENVIRONMENT = "local"

#: Provider API base URLs (see docs/research/ingestion_api_confirmation.md).
DEFAULT_OPENALEX_BASE_URL = "https://api.openalex.org"
DEFAULT_SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1"

#: Provider batch caps: OpenAlex OR-filter (~50 conservative) vs S2 POST /paper/batch (500).
DEFAULT_OPENALEX_BATCH_SIZE = 50
DEFAULT_SEMANTIC_SCHOLAR_BATCH_SIZE = 500


@dataclass(frozen=True)
class ProviderSettings:
    """Per-provider client settings.

    ``api_key`` is injected from the environment only (never read from a
    committed config file). All limits are config-driven so the post-2026
    OpenAlex budget model and S2 rate caps can be tuned without code changes.
    """

    base_url: str
    api_key: str | None = None
    timeout_seconds: float = 30.0
    max_retries: int = 3
    backoff_base_seconds: float = 0.5
    page_size: int = 100
    batch_size: int = 50
    max_pages: int = 50


@dataclass(frozen=True)
class ProviderConfig:
    """Resolved settings for every supported provider."""

    openalex: ProviderSettings
    semantic_scholar: ProviderSettings


def _default_provider_config() -> ProviderConfig:
    return ProviderConfig(
        openalex=ProviderSettings(
            base_url=DEFAULT_OPENALEX_BASE_URL,
            batch_size=DEFAULT_OPENALEX_BATCH_SIZE,
        ),
        semantic_scholar=ProviderSettings(
            base_url=DEFAULT_SEMANTIC_SCHOLAR_BASE_URL,
            batch_size=DEFAULT_SEMANTIC_SCHOLAR_BATCH_SIZE,
        ),
    )


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
    providers: ProviderConfig = field(default_factory=_default_provider_config)

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
        providers=_load_provider_config(file_data.get("providers"), env),
    )
    config.validate()
    return config


def _load_provider_config(
    file_section: object | None, env: Mapping[str, str]
) -> ProviderConfig:
    """Build provider settings from defaults, TOML overrides, and env keys."""
    section = file_section if isinstance(file_section, dict) else {}
    return ProviderConfig(
        openalex=_provider_settings(
            DEFAULT_OPENALEX_BASE_URL,
            default_batch=DEFAULT_OPENALEX_BATCH_SIZE,
            overrides=section.get("openalex"),
            api_key=env.get(f"{ENV_PREFIX}OPENALEX_API_KEY"),
        ),
        semantic_scholar=_provider_settings(
            DEFAULT_SEMANTIC_SCHOLAR_BASE_URL,
            default_batch=DEFAULT_SEMANTIC_SCHOLAR_BATCH_SIZE,
            overrides=section.get("semantic_scholar"),
            api_key=env.get(f"{ENV_PREFIX}SEMANTIC_SCHOLAR_API_KEY"),
        ),
    )


def _provider_settings(
    default_base_url: str,
    *,
    default_batch: int,
    overrides: object | None,
    api_key: str | None,
) -> ProviderSettings:
    """Merge defaults with optional TOML overrides; ``api_key`` comes from env only."""
    over = overrides if isinstance(overrides, dict) else {}
    if "api_key" in over:
        raise ValueError(
            "api_key must not be set in config files; inject it via environment variables"
        )
    return ProviderSettings(
        base_url=_as_str(over.get("base_url")) or default_base_url,
        api_key=api_key,
        timeout_seconds=float(over.get("timeout_seconds", 30.0)),
        max_retries=int(over.get("max_retries", 3)),
        backoff_base_seconds=float(over.get("backoff_base_seconds", 0.5)),
        page_size=int(over.get("page_size", 100)),
        batch_size=int(over.get("batch_size", default_batch)),
        max_pages=int(over.get("max_pages", 50)),
    )


def _as_str(value: object | None) -> str | None:
    """Coerce a TOML scalar to ``str`` or ``None`` if absent."""
    if value is None:
        return None
    return str(value)
