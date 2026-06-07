"""Plugin registry for ZEA."""
from __future__ import annotations

from system_design.plugins.base import ZEAPlugin


class PluginRegistry:
    """Registry that holds and executes system-design plugins in order."""

    def __init__(self) -> None:
        self._plugins: list[ZEAPlugin] = []

    def register(self, plugin: ZEAPlugin) -> None:
        self._plugins.append(plugin)

    def run_all(self, akg: object, repo_path: object) -> object:
        from pathlib import Path
        from system_design.graph.schema import ArchitectureKnowledgeGraph
        assert isinstance(akg, ArchitectureKnowledgeGraph)
        assert isinstance(repo_path, Path)
        for plugin in self._plugins:
            akg = plugin.run(akg, repo_path)
        return akg

    @property
    def plugins(self) -> list[ZEAPlugin]:
        return list(self._plugins)


# Global registry instance
registry = PluginRegistry()
