"""Every module in the ``litgraph`` package must import cleanly."""

from __future__ import annotations

import importlib
import pkgutil

import litgraph


def _all_module_names() -> list[str]:
    names = [litgraph.__name__]
    for module_info in pkgutil.walk_packages(
        litgraph.__path__, prefix=f"{litgraph.__name__}."
    ):
        names.append(module_info.name)
    return names


def test_import_all_modules() -> None:
    module_names = _all_module_names()
    # Sanity: discovery found more than just the top-level package.
    assert len(module_names) > 1
    for name in module_names:
        importlib.import_module(name)
