"""Detect event/messaging systems and domain events."""
from __future__ import annotations

import re
from pathlib import Path

from system_design.core.evidence import Evidence, EvidenceSet, EvidenceType
from system_design.graph.schema import AKGEdge, AKGNode
from system_design.graph.taxonomy import EdgeType, NodeType

# Messaging system signatures
_MESSAGING_SIGNATURES: list[tuple[str, str, str]] = [
    ("kafka|confluent|kafkajs", "Kafka", "msg_kafka"),
    ("rabbitmq|amqplib|pika|aio.pika", "RabbitMQ", "msg_rabbitmq"),
    ("sqs|amazonsqs|boto3.*sqs", "AWS SQS", "msg_sqs"),
    ("sns|amazonsns|boto3.*sns", "AWS SNS", "msg_sns"),
    ("nats|nats.ws", "NATS", "msg_nats"),
    ("pubsub|google.cloud.pubsub", "Google Pub/Sub", "msg_pubsub"),
    ("bull|bullmq", "BullMQ", "msg_bullmq"),
]

# Domain event name patterns
_EVENT_NAME_PATTERNS = [
    # Common event naming: OrderCreated, PaymentCompleted, UserRegistered
    re.compile(r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+(?:Created|Updated|Deleted|Completed|Failed|Cancelled|Processed|Requested|Approved|Rejected|Sent|Received|Published|Consumed))\b"),
    # Event class names
    re.compile(r'(?:class|interface|type)\s+([A-Z][A-Za-z]+Event)\b'),
    # String event names in publish/emit calls
    re.compile(r'(?:emit|publish|send|produce)\s*\(\s*["\']([A-Z_][A-Z_]+)["\']'),
]

_SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".java", ".go", ".cs", ".rb"}


def _detect_messaging_systems(repo_path: Path) -> list[tuple[str, str, list[str]]]:
    """Detect messaging system usage. Returns (system_id, name, sources)."""
    found: dict[str, tuple[str, list[str]]] = {}

    for source_file in repo_path.rglob("*"):
        if source_file.suffix not in _SOURCE_EXTENSIONS and source_file.name not in {
            "requirements.txt", "package.json", "go.mod", "pom.xml"
        }:
            continue
        if any(skip in str(source_file) for skip in ["node_modules", "__pycache__", ".git"]):
            continue
        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue

        rel = str(source_file.relative_to(repo_path))
        for pattern, name, sys_id in _MESSAGING_SIGNATURES:
            if re.search(pattern, content):
                if sys_id not in found:
                    found[sys_id] = (name, [])
                found[sys_id][1].append(rel)

    return [(sys_id, name, sources) for sys_id, (name, sources) in found.items()]


def _detect_domain_events(repo_path: Path, service_nodes: list[AKGNode]) -> dict[str, list[str]]:
    """Detect domain event names from source files. Returns {event_name: [source_files]}."""
    events: dict[str, list[str]] = {}

    for source_file in repo_path.rglob("*"):
        if source_file.suffix not in _SOURCE_EXTENSIONS:
            continue
        if any(skip in str(source_file) for skip in ["node_modules", "__pycache__", ".git", "test"]):
            continue
        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel = str(source_file.relative_to(repo_path))
        for pattern in _EVENT_NAME_PATTERNS:
            for match in pattern.finditer(content):
                event_name = match.group(1)
                if len(event_name) > 5 and event_name not in {"TypeError", "ValueError", "Exception"}:
                    events.setdefault(event_name, []).append(rel)

    # Deduplicate
    return {k: list(set(v)) for k, v in events.items() if len(v) <= 10}


def detect_events(
    repo_path: Path,
    service_nodes: list[AKGNode],
) -> tuple[list[AKGNode], list[AKGEdge]]:
    """Detect messaging systems and domain events."""
    nodes: list[AKGNode] = []
    edges: list[AKGEdge] = []
    repo_id = f"repo_{repo_path.name}"

    # --- Messaging systems ---
    for sys_id, name, sources in _detect_messaging_systems(repo_path):
        node = AKGNode(
            id=sys_id,
            name=name,
            type=NodeType.QUEUE,
            repository=repo_path.name,
            evidence=EvidenceSet(items=[
                Evidence(
                    type=EvidenceType.PACKAGE_DEPENDENCY,
                    description=f"Found {name} dependency in {src}",
                    source=src,
                    confidence=0.9,
                )
                for src in sources[:3]
            ]),
        )
        nodes.append(node)
        anchor = service_nodes[0].id if service_nodes else repo_id
        edges.append(AKGEdge(source_id=anchor, target_id=sys_id, type=EdgeType.CONNECTS_TO))

    # --- Domain events (only if messaging detected or explicit event patterns) ---
    domain_events = _detect_domain_events(repo_path, service_nodes)
    for event_name, sources in list(domain_events.items())[:20]:  # Cap at 20 events
        safe_id = re.sub(r"[^a-z0-9_]", "_", event_name.lower())
        node_id = f"evt_{safe_id}"
        node = AKGNode(
            id=node_id,
            name=event_name,
            type=NodeType.EVENT,
            repository=repo_path.name,
            evidence=EvidenceSet(items=[Evidence(
                type=EvidenceType.EVENT_PUBLICATION,
                description=f"Detected event name '{event_name}'",
                source=sources[0],
                confidence=0.7,
            )]),
        )
        nodes.append(node)

        # Heuristic: service that publishes — inferred from file location
        for svc in service_nodes:
            if svc.path and any(svc.path in src for src in sources):
                edges.append(AKGEdge(source_id=svc.id, target_id=node_id, type=EdgeType.PUBLISHES))
                break
        else:
            anchor = service_nodes[0].id if service_nodes else repo_id
            edges.append(AKGEdge(source_id=anchor, target_id=node_id, type=EdgeType.PUBLISHES))

    return nodes, edges
