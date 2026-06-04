"""Node and Edge type taxonomy for the Architecture Knowledge Graph."""
from __future__ import annotations

from enum import Enum


class NodeType(str, Enum):
    # Application layer
    FRONTEND = "frontend"
    BACKEND = "backend"
    MONOLITH = "monolith"
    GATEWAY = "gateway"
    WORKER = "worker"

    # Service layer
    SERVICE = "service"

    # API layer
    REST_API = "rest_api"
    GRAPHQL_API = "graphql_api"
    GRPC_API = "grpc_api"
    WEBHOOK = "webhook"

    # Data layer
    DATABASE = "database"
    CACHE = "cache"

    # Messaging layer
    QUEUE = "queue"
    TOPIC = "topic"
    EVENT = "event"

    # Domain layer
    DOMAIN = "domain"

    # Infrastructure layer
    CLUSTER = "cluster"
    NAMESPACE = "namespace"
    POD = "pod"
    LOAD_BALANCER = "load_balancer"
    VPC = "vpc"

    # Organizational layer
    TEAM = "team"

    # External
    EXTERNAL_SYSTEM = "external_system"

    # Repository (root)
    REPOSITORY = "repository"


class EdgeType(str, Enum):
    # Dependency
    DEPENDS_ON = "DEPENDS_ON"
    IMPORTS = "IMPORTS"
    REFERENCES = "REFERENCES"

    # Communication
    CALLS = "CALLS"
    INVOKES = "INVOKES"
    CONNECTS_TO = "CONNECTS_TO"

    # Data
    READS = "READS"
    WRITES = "WRITES"
    OWNS = "OWNS"

    # Events
    PUBLISHES = "PUBLISHES"
    CONSUMES = "CONSUMES"

    # Organization
    CONTAINS = "CONTAINS"
    BELONGS_TO = "BELONGS_TO"
    OWNED_BY = "OWNED_BY"
    DEPLOYED_IN = "DEPLOYED_IN"
