"""Artifact paths must always resolve under the project root."""

from __future__ import annotations

from pathlib import Path

import pytest

from litgraph.config import Config, load_config


def test_default_artifact_paths_are_under_project_root(project_root: Path) -> None:
    config = load_config(env={})
    for path in config.artifact_dirs():
        assert path.resolve().is_relative_to(project_root)


def test_validate_rejects_path_outside_project_root(project_root: Path) -> None:
    outside = Config(
        project_root=project_root,
        artifacts_dir=Path("/tmp/litgraph_outside_root"),
        environment="test",
    )
    with pytest.raises(ValueError):
        outside.validate()


def test_load_config_rejects_escaping_relative_path() -> None:
    with pytest.raises(ValueError):
        load_config(env={"LITGRAPH_ARTIFACTS_DIR": "../escapes_root"})
