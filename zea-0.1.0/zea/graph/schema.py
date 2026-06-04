"""Pydantic schema for AKG nodes and edges."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field
from zea.graph.taxonomy import EdgeType, NodeType
from zea.core.evidence import EvidenceSet


class AKGNode(BaseModel):
    """A node in the Architecture Knowledge Graph."""

    id: str = Field(description="Unique node identifier, e.g. 'svc_order'")
    name: str
    type: NodeType
    language: str | None = None
    framework: str | None = None
    repository: str | None = None
    owner: str | None = None
    path: str | None = None  # Source path in repository
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence: EvidenceSet = Field(default_factory=EvidenceSet)
    tags: list[str] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class AKGEdge(BaseModel):
    """A directed edge in the Architecture Knowledge Graph."""

    source_id: str
    target_id: str
    type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)
    evidence: EvidenceSet = Field(default_factory=EvidenceSet)

    @property
    def id(self) -> str:
        return f"{self.source_id}--{self.type}--{self.target_id}"

    model_config = ConfigDict(use_enum_values=True)


class ArchitectureKnowledgeGraph(BaseModel):
    """
    The canonical Architecture Knowledge Graph.

    This is the central artifact of ZEA. All outputs are derived from it.
    """

    repository_name: str
    repository_path: str
    nodes: list[AKGNode] = Field(default_factory=list)
    edges: list[AKGEdge] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def get_node(self, node_id: str) -> AKGNode | None:
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_edges_from(self, node_id: str) -> list[AKGEdge]:
        return [e for e in self.edges if e.source_id == node_id]

    def get_edges_to(self, node_id: str) -> list[AKGEdge]:
        return [e for e in self.edges if e.target_id == node_id]

    def nodes_by_type(self, node_type: NodeType) -> list[AKGNode]:
        return [n for n in self.nodes if n.type == node_type]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    model_config = ConfigDict(use_enum_values=True)
