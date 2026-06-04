"""Architecture Inference Engine — orchestrates all inference detectors."""
from __future__ import annotations

from pathlib import Path

from zea.core.logging import get_logger
from zea.graph.schema import ArchitectureKnowledgeGraph
from zea.graph.taxonomy import NodeType
from zea.inference.api_detector import detect_apis
from zea.inference.database_detector import detect_databases
from zea.inference.dependency_detector import detect_dependencies
from zea.inference.event_detector import detect_events
from zea.inference.service_detector import detect_services

logger = get_logger(__name__)


class InferenceEngine:
    """
    Milestone 3: Architecture Inference.

    Takes an AKG (from Milestone 2) and enriches it with:
    - Services
    - APIs
    - Databases
    - Events / Messaging

    All inferences include evidence (file paths, patterns, confidence).
    """

    def __init__(self, akg: ArchitectureKnowledgeGraph, repo_path: Path) -> None:
        self.akg = akg
        self.repo_path = repo_path.resolve()

    def run(self) -> ArchitectureKnowledgeGraph:
        logger.info("Running Architecture Inference...")

        repo_id = f"repo_{self.akg.repository_name}"
        primary_lang = self.akg.metadata.get("primary_language", "unknown")

        # Step 1: Detect services
        logger.info("  → Detecting services")
        svc_nodes, svc_edges = detect_services(self.repo_path, repo_id, primary_lang)
        for node in svc_nodes:
            self.akg.nodes.append(node)
        for edge in svc_edges:
            self.akg.edges.append(edge)
        logger.info(f"     Found {len(svc_nodes)} services")

        service_nodes = self.akg.nodes_by_type(NodeType.SERVICE)

        # Step 2: Detect APIs
        logger.info("  → Detecting APIs")
        api_nodes, api_edges = detect_apis(self.repo_path, service_nodes)
        for node in api_nodes:
            self.akg.nodes.append(node)
        for edge in api_edges:
            self.akg.edges.append(edge)
        logger.info(f"     Found {len(api_nodes)} API endpoints")

        # Step 3: Detect databases
        logger.info("  → Detecting databases")
        db_nodes, db_edges = detect_databases(self.repo_path, service_nodes)
        for node in db_nodes:
            self.akg.nodes.append(node)
        for edge in db_edges:
            self.akg.edges.append(edge)
        logger.info(f"     Found {len(db_nodes)} databases")

        # Step 4: Detect events
        logger.info("  → Detecting events and messaging")
        evt_nodes, evt_edges = detect_events(self.repo_path, service_nodes)
        for node in evt_nodes:
            self.akg.nodes.append(node)
        for edge in evt_edges:
            self.akg.edges.append(edge)
        logger.info(f"     Found {len(evt_nodes)} events/queues")

        # Step 5: Detect inter-service dependencies (CALLS edges)
        all_service_nodes = (
            self.akg.nodes_by_type(NodeType.SERVICE)
            + self.akg.nodes_by_type(NodeType.FRONTEND)
            + self.akg.nodes_by_type(NodeType.BACKEND)
            + self.akg.nodes_by_type(NodeType.GATEWAY)
        )
        logger.info("  → Detecting inter-service dependencies")
        dep_edges = detect_dependencies(self.repo_path, all_service_nodes)
        for edge in dep_edges:
            self.akg.edges.append(edge)
        logger.info(f"     Found {len(dep_edges)} inter-service CALLS edges")

        logger.info(
            f"Inference complete: {self.akg.node_count} nodes, {self.akg.edge_count} edges"
        )
        return self.akg
