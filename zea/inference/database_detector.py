"""Detect database usage from dependencies and source code."""
from __future__ import annotations

import re
from pathlib import Path

from zea.core.evidence import Evidence, EvidenceSet, EvidenceType
from zea.graph.schema import AKGEdge, AKGNode
from zea.graph.taxonomy import EdgeType, NodeType

# Database signatures: (package/import pattern, db_name, node_id_prefix, metadata)
_DB_SIGNATURES: list[tuple[str, str, str, dict[str, str]]] = [
    # PostgreSQL
    ("psycopg2|psycopg|asyncpg|pg|postgres|postgresql", "PostgreSQL", "db_postgres", {"engine": "postgresql"}),
    ("typeorm.*postgres|sequelize.*postgres|prisma.*postgresql|pg_pool", "PostgreSQL", "db_postgres", {"engine": "postgresql"}),
    # MySQL
    ("mysql|mysql2|pymysql|aiomysql", "MySQL", "db_mysql", {"engine": "mysql"}),
    # MongoDB
    ("mongodb|mongoose|pymongo|motor|mongoclient", "MongoDB", "db_mongodb", {"engine": "mongodb"}),
    # Redis
    ("redis|ioredis|aioredis|rediscluster", "Redis", "db_redis", {"engine": "redis", "type": "cache"}),
    # DynamoDB
    ("dynamodb|dynamoose|pynamodb", "DynamoDB", "db_dynamodb", {"engine": "dynamodb"}),
    # SQLite
    ("sqlite|sqlite3|aiosqlite", "SQLite", "db_sqlite", {"engine": "sqlite"}),
    # Elasticsearch
    ("elasticsearch|elastic", "Elasticsearch", "db_elasticsearch", {"engine": "elasticsearch"}),
    # Cassandra
    ("cassandra|datastax", "Cassandra", "db_cassandra", {"engine": "cassandra"}),
]

_SOURCE_EXTENSIONS = {".py", ".ts", ".js", ".java", ".go", ".cs", ".rb", ".env", ".yaml", ".yml"}
_ENV_DB_PATTERN = re.compile(
    r"(?:DATABASE_URL|DB_HOST|POSTGRES_HOST|MYSQL_HOST|MONGO_URI|REDIS_URL|MONGODB_URI)[\s=:]+(.+)",
    re.IGNORECASE,
)


def _scan_for_db_usage(repo_path: Path) -> dict[str, list[str]]:
    """Scan source files for database usage signatures. Returns {db_id: [evidence_sources]}."""
    found: dict[str, list[str]] = {}

    for source_file in repo_path.rglob("*"):
        if source_file.suffix not in _SOURCE_EXTENSIONS:
            continue
        if any(skip in str(source_file) for skip in ["node_modules", "__pycache__", ".git"]):
            continue
        try:
            content = source_file.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue

        rel = str(source_file.relative_to(repo_path))
        for pattern, _, db_id, _ in _DB_SIGNATURES:
            if re.search(pattern, content):
                found.setdefault(db_id, []).append(rel)

    # Also check env files
    for env_file in list(repo_path.rglob(".env*")) + list(repo_path.rglob("*.env")):
        try:
            content = env_file.read_text(encoding="utf-8", errors="ignore")
            for match in _ENV_DB_PATTERN.finditer(content):
                val = match.group(1).lower()
                for pattern, _, db_id, _ in _DB_SIGNATURES:
                    if re.search(pattern.split("|")[0], val):
                        found.setdefault(db_id, []).append(str(env_file.relative_to(repo_path)))
        except Exception:
            pass

    return found


def detect_databases(
    repo_path: Path,
    service_nodes: list[AKGNode],
) -> tuple[list[AKGNode], list[AKGEdge]]:
    """Detect databases from dependency and source analysis."""
    nodes: list[AKGNode] = []
    edges: list[AKGEdge] = []

    db_usage = _scan_for_db_usage(repo_path)
    sig_map = {db_id: (name, meta) for _, name, db_id, meta in _DB_SIGNATURES}

    for db_id, sources in db_usage.items():
        if db_id not in sig_map:
            continue
        db_name, metadata = sig_map[db_id]

        node = AKGNode(
            id=db_id,
            name=db_name,
            type=NodeType.DATABASE if metadata.get("type") != "cache" else NodeType.CACHE,
            repository=repo_path.name,
            metadata=metadata,
            evidence=EvidenceSet(items=[
                Evidence(
                    type=EvidenceType.DATABASE_USAGE,
                    description=f"Found {db_name} usage in {src}",
                    source=src,
                    confidence=0.85,
                )
                for src in sources[:5]
            ]),
        )
        nodes.append(node)

        # Connect all services to this database (they all use it)
        for svc in service_nodes:
            edges.append(AKGEdge(
                source_id=svc.id,
                target_id=db_id,
                type=EdgeType.READS,
                metadata={"inferred": True},
            ))

        # Also connect repo if no services
        if not service_nodes:
            edges.append(AKGEdge(
                source_id=f"repo_{repo_path.name}",
                target_id=db_id,
                type=EdgeType.READS,
            ))

    return nodes, edges
