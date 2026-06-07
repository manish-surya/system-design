"""Detect services from repository structure and naming conventions."""
from __future__ import annotations

import re
from pathlib import Path

from system_design.core.evidence import Evidence, EvidenceSet, EvidenceType
from system_design.graph.schema import AKGEdge, AKGNode
from system_design.graph.taxonomy import EdgeType, NodeType

# Service naming conventions in directory names
SERVICE_PATTERNS = [
    re.compile(r"^(.+)[-_](service|svc|api|server|app|worker|job|daemon)$", re.IGNORECASE),
    re.compile(r"^(service|svc)[-_](.+)$", re.IGNORECASE),
]

# Directories that strongly suggest a service boundary
SERVICE_INDICATORS = {
    "controllers", "controller",
    "routes", "router",
    "handlers", "handler",
    "endpoints", "endpoint",
    "api", "apis",
    "main.py", "main.go", "main.ts", "index.ts", "app.py", "app.ts",
    "server.py", "server.go", "server.ts",
    "Dockerfile",
}

# Paths that are NOT services
NON_SERVICE_DIRS = {
    "common", "shared", "utils", "helpers", "lib", "libs",
    "config", "configs", "scripts", "tools", "docs",
    "tests", "test", "__tests__", "spec",
    "migrations", "seeds", "fixtures",
    "node_modules", "__pycache__", ".git",
}


def _name_to_service_name(dir_name: str) -> str:
    """Convert a directory name to a human-readable service name."""
    for pattern in SERVICE_PATTERNS:
        m = pattern.match(dir_name)
        if m:
            parts = [p for p in m.groups() if p and p.lower() not in {"service", "svc", "api", "server", "app"}]
            if parts:
                return " ".join(p.title() for p in re.split(r"[-_]", parts[0]))
    # Fallback: title-case the dir name
    return " ".join(p.title() for p in re.split(r"[-_]", dir_name))


def detect_services(
    repo_path: Path,
    repo_id: str,
    primary_language: str,
) -> tuple[list[AKGNode], list[AKGEdge]]:
    """
    Infer services from the repository structure.

    Heuristics:
    1. Top-level directories that look like services (name-based)
    2. Directories containing service indicators (Dockerfile, main.*, routes/, etc.)
    3. Monorepo detection (packages/, apps/, services/ directories)
    """
    nodes: list[AKGNode] = []
    edges: list[AKGEdge] = []
    seen_ids: set[str] = set()

    def make_service_node(
        dir_path: Path,
        service_name: str,
        evidence_items: list[Evidence],
    ) -> AKGNode:
        safe_id = re.sub(r"[^a-z0-9_]", "_", service_name.lower().replace(" ", "_"))
        node_id = f"svc_{safe_id}"
        return AKGNode(
            id=node_id,
            name=f"{service_name} Service",
            type=NodeType.SERVICE,
            language=primary_language,
            repository=repo_path.name,
            path=str(dir_path.relative_to(repo_path)),
            evidence=EvidenceSet(items=evidence_items),
        )

    # --- Strategy 1: Monorepo containers ---
    monorepo_containers = ["services", "apps", "packages", "modules", "microservices"]
    for container in monorepo_containers:
        container_path = repo_path / container
        if container_path.is_dir():
            for subdir in container_path.iterdir():
                if subdir.is_dir() and subdir.name not in NON_SERVICE_DIRS:
                    svc_name = _name_to_service_name(subdir.name)
                    evidence = [Evidence(
                        type=EvidenceType.DIRECTORY_STRUCTURE,
                        description=f"Directory '{subdir.name}' inside '{container}/' monorepo container",
                        source=str(subdir.relative_to(repo_path)),
                        confidence=0.85,
                    )]

                    # Boost confidence if service indicators are present
                    for indicator in SERVICE_INDICATORS:
                        if (subdir / indicator).exists():
                            evidence.append(Evidence(
                                type=EvidenceType.FILE_PATTERN,
                                description=f"Found '{indicator}' inside service directory",
                                source=str((subdir / indicator).relative_to(repo_path)),
                                confidence=0.9,
                            ))

                    node = make_service_node(subdir, svc_name, evidence)
                    if node.id not in seen_ids:
                        seen_ids.add(node.id)
                        nodes.append(node)
                        edges.append(AKGEdge(
                            source_id=repo_id,
                            target_id=node.id,
                            type=EdgeType.CONTAINS,
                        ))

    # --- Strategy 2: Top-level service directories ---
    if not nodes:  # Only if monorepo detection found nothing
        for subdir in repo_path.iterdir():
            if not subdir.is_dir() or subdir.name in NON_SERVICE_DIRS:
                continue
            if subdir.name.startswith("."):
                continue

            evidence: list[Evidence] = []

            # Check name pattern
            for pattern in SERVICE_PATTERNS:
                if pattern.match(subdir.name):
                    evidence.append(Evidence(
                        type=EvidenceType.NAMING_CONVENTION,
                        description=f"Directory name '{subdir.name}' matches service naming convention",
                        source=str(subdir.relative_to(repo_path)),
                        confidence=0.75,
                    ))

            # Check for service indicators
            for indicator in SERVICE_INDICATORS:
                if (subdir / indicator).exists():
                    evidence.append(Evidence(
                        type=EvidenceType.FILE_PATTERN,
                        description=f"Found '{indicator}' inside directory",
                        source=str((subdir / indicator).relative_to(repo_path)),
                        confidence=0.85,
                    ))

            # Require at least one piece of evidence
            if evidence:
                svc_name = _name_to_service_name(subdir.name)
                node = make_service_node(subdir, svc_name, evidence)
                if node.id not in seen_ids:
                    seen_ids.add(node.id)
                    nodes.append(node)
                    edges.append(AKGEdge(
                        source_id=repo_id,
                        target_id=node.id,
                        type=EdgeType.CONTAINS,
                    ))

    return nodes, edges
