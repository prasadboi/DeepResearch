"""Configuration loads from a TOML fixture through the single config module."""

from __future__ import annotations

from pathlib import Path

from litgraph.config import load_config


def test_config_loads_from_fixture(fixtures_dir: Path, project_root: Path) -> None:
    config = load_config(fixtures_dir / "config.fixture.toml", env={})

    assert config.environment == "test"
    assert config.artifacts_dir == project_root / "artifacts_test"
    assert config.project_root == project_root
    # Values from the fixture must resolve under the project root.
    assert config.artifacts_dir.is_relative_to(project_root)


def test_env_overrides_default_when_no_file() -> None:
    config = load_config(env={"LITGRAPH_ENVIRONMENT": "ci"})
    assert config.environment == "ci"


def test_file_value_takes_precedence_over_env(fixtures_dir: Path) -> None:
    config = load_config(
        fixtures_dir / "config.fixture.toml",
        env={"LITGRAPH_ENVIRONMENT": "ignored"},
    )
    assert config.environment == "test"
