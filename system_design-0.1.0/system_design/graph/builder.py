"""NetworkX-based AKG builder."""
from __future__ import annotations

import networkx as nx

from system_design.core.evidence import Evidence, EvidenceSet, EvidenceType
from system_design.core.logging import get_logger
from system_design.discovery.models import RepositoryInventory
from system_design.graph.schema import AKGEdge, AKGNode, ArchitectureKnowledgeGraph
from system_design.graph.taxonomy import EdgeType, NodeType

logger = get_logger(__name__)


class AKGBuilder:
    """
    Builds the Architecture Knowledge Graph from a RepositoryInventory.

    This is the Milestone 2 graph builder — it creates a skeleton AKG
    from discovery data. Architecture Inference (Milestone 3) will
    enrich it with services, APIs, databases, and events.
    """

    def __init__(self, inventory: RepositoryInventory) -> None:
        self.inventory = inventory
        self._nx_graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, AKGNode] = {}
        self._edges: list[AKGEdge] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> ArchitectureKnowledgeGraph:
        """Build and return the AKG from the repository inventory."""
        logger.info(f"Building AKG for: {self.inventory.repository_name}")

        self._add_repository_node()
        self._add_language_nodes()
        self._add_framework_nodes()
        self._add_infrastructure_nodes()

        akg = ArchitectureKnowledgeGraph(
            repository_name=self.inventory.repository_name,
            repository_path=self.inventory.repository_path,
            nodes=list(self._nodes.values()),
            edges=self._edges,
            metadata={
                "total_files": self.inventory.total_files,
                "has_tests": self.inventory.has_tests,
                "has_ci": self.inventory.has_ci,
                "primary_language": self.inventory.primary_language,
            },
        )

        logger.info(f"AKG built: {akg.node_count} nodes, {akg.edge_count} edges")
        return akg

    def add_node(self, node: AKGNode) -> None:
        self._nodes[node.id] = node
        self._nx_graph.add_node(node.id, **{"type": node.type, "name": node.name})

    def add_edge(self, edge: AKGEdge) -> None:
        self._edges.append(edge)
        self._nx_graph.add_edge(edge.source_id, edge.target_id, type=edge.type)

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _make_evidence(self, description: str, source: str, confidence: float = 0.8) -> EvidenceSet:
        return EvidenceSet(items=[Evidence(
            type=EvidenceType.DIRECTORY_STRUCTURE,
            description=description,
            source=source,
            confidence=confidence,
        )])

    def _add_repository_node(self) -> None:
        node = AKGNode(
            id=f"repo_{self.inventory.repository_name}",
            name=self.inventory.repository_name,
            type=NodeType.REPOSITORY,
            language=self.inventory.primary_language,
            path=self.inventory.repository_path,
            evidence=self._make_evidence(
                "Root repository node",
                self.inventory.repository_path,
                confidence=1.0,
            ),
        )
        self.add_node(node)

    def _add_language_nodes(self) -> None:
        """Attach language metadata to repository node (not separate nodes)."""
        # Languages are metadata on the repo node, not separate graph nodes
        repo_node_id = f"repo_{self.inventory.repository_name}"
        if repo_node_id in self._nodes:
            self._nodes[repo_node_id].metadata["languages"] = [
                {"language": ls.language, "file_count": ls.file_count}
                for ls in self.inventory.languages
            ]

    def _add_framework_nodes(self) -> None:
        """Infer application type from frameworks and add nodes."""
        repo_id = f"repo_{self.inventory.repository_name}"
        framework_names = {f.framework for f in self.inventory.frameworks}

        frontend_frameworks = {"react", "nextjs", "angular", "vue"}
        backend_frameworks = {"fastapi", "django", "flask", "express", "nestjs", "spring", "gin", "echo", "fiber"}

        has_frontend = bool(framework_names & frontend_frameworks)
        has_backend = bool(framework_names & backend_frameworks)

        if has_frontend:
            node_id = f"app_frontend_{self.inventory.repository_name}"
            node_type = NodeType.FRONTEND
            fw = next(f for f in self.inventory.frameworks if f.framework in frontend_frameworks)
            self.add_node(AKGNode(
                id=node_id,
                name=f"{self.inventory.repository_name} (Frontend)",
                type=node_type,
                framework=fw.framework,
                repository=self.inventory.repository_name,
                evidence=EvidenceSet(items=[Evidence(
                    type=EvidenceType.PACKAGE_DEPENDENCY,
                    description=f"Detected frontend framework: {fw.framework}",
                    source=fw.evidence[0] if fw.evidence else "package.json",
                    confidence=fw.confidence,
                )]),
            ))
            self.add_edge(AKGEdge(
                source_id=repo_id,
                target_id=node_id,
                type=EdgeType.CONTAINS,
            ))

        if has_backend:
            node_id = f"app_backend_{self.inventory.repository_name}"
            fw = next(f for f in self.inventory.frameworks if f.framework in backend_frameworks)
            self.add_node(AKGNode(
                id=node_id,
                name=f"{self.inventory.repository_name} (Backend)",
                type=NodeType.BACKEND,
                framework=fw.framework,
                repository=self.inventory.repository_name,
                evidence=EvidenceSet(items=[Evidence(
                    type=EvidenceType.PACKAGE_DEPENDENCY,
                    description=f"Detected backend framework: {fw.framework}",
                    source=fw.evidence[0] if fw.evidence else "dependency file",
                    confidence=fw.confidence,
                )]),
            ))
            self.add_edge(AKGEdge(
                source_id=repo_id,
                target_id=node_id,
                type=EdgeType.CONTAINS,
            ))

    def _add_infrastructure_nodes(self) -> None:
        """Add infrastructure nodes from detected infra types."""
        repo_id = f"repo_{self.inventory.repository_name}"
        from system_design.discovery.models import InfrastructureType

        infra_type_map = {
            InfrastructureType.KUBERNETES: (NodeType.CLUSTER, "Kubernetes Cluster"),
            InfrastructureType.DOCKER_COMPOSE: (NodeType.CLUSTER, "Docker Compose Environment"),
        }

        for infra in self.inventory.infrastructure:
            if infra.type in infra_type_map:
                node_type, label = infra_type_map[infra.type]
                node_id = f"infra_{infra.type}_{self.inventory.repository_name}"
                self.add_node(AKGNode(
                    id=node_id,
                    name=label,
                    type=node_type,
                    repository=self.inventory.repository_name,
                    evidence=self._make_evidence(
                        f"Found {infra.type} configuration",
                        infra.files[0] if infra.files else "infra config",
                        confidence=0.9,
                    ),
                    metadata={"files": infra.files},
                ))
                self.add_edge(AKGEdge(
                    source_id=repo_id,
                    target_id=node_id,
                    type=EdgeType.DEPLOYED_IN,
                ))

    def to_networkx(self) -> nx.DiGraph:
        return self._nx_graph
