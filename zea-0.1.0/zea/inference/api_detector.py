"""Detect API routes and endpoints from source files."""
from __future__ import annotations

import re
from pathlib import Path

from zea.core.evidence import Evidence, EvidenceSet, EvidenceType
from zea.graph.schema import AKGEdge, AKGNode
from zea.graph.taxonomy import EdgeType, NodeType

# Regex patterns for route detection per language/framework
_ROUTE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # FastAPI / Flask
    ("python", re.compile(r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)),
    # Express / NestJS
    ("javascript", re.compile(r'(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)),
    # NestJS decorators
    ("nestjs", re.compile(r'@(Get|Post|Put|Delete|Patch)\s*\(\s*["\']?([^"\')\s]*)["\']?\s*\)', re.IGNORECASE)),
    # Spring
    ("java", re.compile(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE)),
    # Go Gin/Echo
    ("go", re.compile(r'(?:r|e|g)\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*"([^"]+)"', re.IGNORECASE)),
]

_SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".java", ".go", ".cs", ".rb", ".php"}


def _method_to_str(m: str) -> str:
    mapping = {
        "getmapping": "GET", "postmapping": "POST",
        "putmapping": "PUT", "deletemapping": "DELETE",
        "requestmapping": "ANY",
    }
    return mapping.get(m.lower(), m.upper())


def detect_apis(
    repo_path: Path,
    service_nodes: list[AKGNode],
) -> tuple[list[AKGNode], list[AKGEdge]]:
    """
    Detect REST API endpoints from source files.

    For each detected route, creates an AKGNode of type REST_API
    and connects it to the owning service node.
    """
    nodes: list[AKGNode] = []
    edges: list[AKGEdge] = []
    seen_paths: set[str] = set()

    def find_service_for_file(file_path: Path) -> AKGNode | None:
        """Find which service node owns this file by path prefix."""
        for svc in service_nodes:
            if svc.path and str(file_path).startswith(str(repo_path / svc.path)):
                return svc
        return None

    for source_file in repo_path.rglob("*"):
        if source_file.suffix not in _SOURCE_EXTENSIONS:
            continue
        if any(skip in str(source_file) for skip in ["node_modules", "__pycache__", ".git", "test", "spec"]):
            continue

        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        file_routes: list[tuple[str, str]] = []
        for _, pattern in _ROUTE_PATTERNS:
            for match in pattern.finditer(content):
                method = _method_to_str(match.group(1))
                path = match.group(2) if match.lastindex >= 2 else "/"
                if path and path not in ("", "/"):
                    file_routes.append((method, path))

        for method, route_path in file_routes:
            route_key = f"{method}:{route_path}"
            if route_key in seen_paths:
                continue
            seen_paths.add(route_key)

            rel_file = str(source_file.relative_to(repo_path))
            safe_path = re.sub(r"[^a-z0-9_]", "_", route_path.lower().strip("/").replace("/", "_"))
            node_id = f"api_{method.lower()}_{safe_path[:40]}"

            api_node = AKGNode(
                id=node_id,
                name=f"{method} {route_path}",
                type=NodeType.REST_API,
                path=rel_file,
                repository=repo_path.name,
                metadata={"method": method, "route": route_path},
                evidence=EvidenceSet(items=[Evidence(
                    type=EvidenceType.API_ROUTE,
                    description=f"Detected route '{method} {route_path}' in {rel_file}",
                    source=rel_file,
                    confidence=0.9,
                )]),
            )
            nodes.append(api_node)

            # Link to owning service (if found), else link to repo
            owner = find_service_for_file(source_file)
            source_id = owner.id if owner else f"repo_{repo_path.name}"
            edges.append(AKGEdge(
                source_id=source_id,
                target_id=node_id,
                type=EdgeType.CONTAINS,
            ))

    return nodes, edges
