"""
Detect inter-service dependencies — HTTP calls, imports, env-based service URLs.
Produces CALLS edges between services, giving the graph meaningful connectivity.
"""
from __future__ import annotations

import re
from pathlib import Path

from system_design.core.evidence import Evidence, EvidenceSet, EvidenceType
from system_design.graph.schema import AKGEdge, AKGNode
from system_design.graph.taxonomy import EdgeType

_SOURCE_EXT = {".py", ".ts", ".js", ".java", ".go", ".cs", ".rb", ".php"}

# Patterns that suggest one service is calling another
_HTTP_CLIENT_PATTERNS = [
    # axios, fetch, requests, httpx, got, needle, superagent
    re.compile(r'(?:axios|fetch|requests|httpx|got|needle|http)\s*\.\s*(?:get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']', re.IGNORECASE),
    # URL env vars or constants like SERVICE_URL, ORDER_SERVICE_URL
    re.compile(r'(?:process\.env\.|os\.environ)\[?["\']?([A-Z_]+_(?:URL|HOST|ENDPOINT|SERVICE))["\']?\]?', re.IGNORECASE),
    # Go http.Get / http.Post
    re.compile(r'http\s*\.\s*(?:Get|Post|Put|Delete)\s*\(["\']([^"\']+)["\']', re.IGNORECASE),
    # Java RestTemplate, WebClient, OkHttp
    re.compile(r'(?:restTemplate|webClient|okHttpClient)\s*\.\s*(?:getForObject|postForObject|exchange|get|post)\s*\(["\']([^"\']+)["\']', re.IGNORECASE),
    # Generic service name references in URLs: "http://order-service", "http://billing"
    re.compile(r'https?://([a-z][a-z0-9-]+)(?::\d+)?(?:/[^\s"\']*)?', re.IGNORECASE),
]

# Micro-URL patterns that look like internal service calls (skip external domains)
_EXTERNAL_DOMAINS = {
    "github", "google", "aws", "azure", "stripe", "twilio", "sendgrid",
    "cloudflare", "fastly", "cdn", "s3", "lambda", "googleapis",
    "example", "localhost", "127.0.0", "0.0.0",
}


def _is_internal(host: str) -> bool:
    h = host.lower()
    return not any(ext in h for ext in _EXTERNAL_DOMAINS)


def _service_name_slug(name: str) -> str:
    """Normalize a service name to match service node id pattern."""
    return re.sub(r"[^a-z0-9]", "_", name.lower().strip())


def detect_dependencies(
    repo_path: Path,
    service_nodes: list[AKGNode],
) -> list[AKGEdge]:
    """
    Scan source files for HTTP client calls and service URL references.
    Generate CALLS edges between service nodes.
    """
    if not service_nodes:
        return []

    edges: list[AKGEdge] = []
    seen_pairs: set[tuple[str, str]] = set()

    # Build lookup: slug → node_id for quick matching
    svc_slugs: dict[str, str] = {}
    for svc in service_nodes:
        slug = _service_name_slug(svc.name.replace(" Service", "").replace(" service", ""))
        svc_slugs[slug] = svc.id
        # Also index by id fragments
        for part in svc.id.split("_"):
            if len(part) > 3:
                svc_slugs[part] = svc.id

    def find_service_for_path(file_path: Path) -> AKGNode | None:
        for svc in service_nodes:
            if svc.path and str(file_path).startswith(str(repo_path / svc.path)):
                return svc
        return None

    def find_called_service(url_or_name: str) -> AKGNode | None:
        """Try to match a URL fragment or name to a service node."""
        # Extract hostname from URL
        m = re.match(r'https?://([^/:]+)', url_or_name)
        if m:
            host = m.group(1)
        else:
            host = url_or_name

        if not _is_internal(host):
            return None

        host_slug = _service_name_slug(host)
        # Direct slug match
        if host_slug in svc_slugs:
            return next((s for s in service_nodes if s.id == svc_slugs[host_slug]), None)
        # Partial match — host contains service name fragment
        for slug, svc_id in svc_slugs.items():
            if slug and (slug in host_slug or host_slug in slug):
                return next((s for s in service_nodes if s.id == svc_id), None)
        return None

    for source_file in repo_path.rglob("*"):
        if source_file.suffix not in _SOURCE_EXT:
            continue
        if any(skip in str(source_file) for skip in
               ["node_modules", "__pycache__", ".git", "test", "spec", "mock"]):
            continue

        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        caller = find_service_for_path(source_file)
        if not caller:
            continue

        rel = str(source_file.relative_to(repo_path))

        for pattern in _HTTP_CLIENT_PATTERNS:
            for match in pattern.finditer(content):
                target_hint = match.group(1)
                callee = find_called_service(target_hint)
                if callee and callee.id != caller.id:
                    pair = (caller.id, callee.id)
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        edges.append(AKGEdge(
                            source_id=caller.id,
                            target_id=callee.id,
                            type=EdgeType.CALLS,
                            evidence=EvidenceSet(items=[Evidence(
                                type=EvidenceType.FILE_CONTENT,
                                description=f"HTTP call pattern '{target_hint}' in {rel}",
                                source=rel,
                                confidence=0.75,
                            )]),
                        ))

    # If no inter-service edges found via HTTP pattern scanning,
    # infer topology from naming conventions (common in microservice repos):
    # services that share the same domain prefix likely communicate
    if not edges and len(service_nodes) > 1:
        _infer_topology_from_names(service_nodes, edges, seen_pairs)

    return edges


def _infer_topology_from_names(
    service_nodes: list[AKGNode],
    edges: list[AKGEdge],
    seen_pairs: set[tuple[str, str]],
) -> None:
    """
    Fallback: connect services that likely communicate based on naming.
    Gateway → all services, services → shared data services.
    """
    gateways   = [s for s in service_nodes if "gateway" in s.id or "gateway" in s.name.lower()]
    frontends  = [s for s in service_nodes if s.type in {"frontend"}]
    backends   = [s for s in service_nodes if s.type in {"service", "backend", "microservice"}]

    # Gateway/frontend calls all backend services
    for caller in gateways + frontends:
        for callee in backends:
            if caller.id == callee.id:
                continue
            pair = (caller.id, callee.id)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                edges.append(AKGEdge(
                    source_id=caller.id,
                    target_id=callee.id,
                    type=EdgeType.CALLS,
                    evidence=EvidenceSet(items=[Evidence(
                        type=EvidenceType.NAMING_CONVENTION,
                        description="Inferred gateway→service topology from naming",
                        source="naming_convention",
                        confidence=0.5,
                    )]),
                ))
