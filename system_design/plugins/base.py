"""Plugin base classes for system-design extensibility."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from system_design.graph.schema import ArchitectureKnowledgeGraph


class ZEAPlugin(ABC):
    """Base class for all system-design plugins."""

    name: str = "unnamed_plugin"
    version: str = "0.1.0"
    description: str = ""

    @abstractmethod
    def run(self, akg: ArchitectureKnowledgeGraph, repo_path: Path) -> ArchitectureKnowledgeGraph:
        """Execute the plugin against the AKG and return the enriched graph."""
        ...


class DetectorPlugin(ZEAPlugin):
    """Plugin that adds nodes/edges to the AKG."""

    @abstractmethod
    def run(self, akg: ArchitectureKnowledgeGraph, repo_path: Path) -> ArchitectureKnowledgeGraph:
        ...


class AnalyzerPlugin(ZEAPlugin):
    """Plugin that adds metadata/insights to the AKG."""

    @abstractmethod
    def run(self, akg: ArchitectureKnowledgeGraph, repo_path: Path) -> ArchitectureKnowledgeGraph:
        ...
