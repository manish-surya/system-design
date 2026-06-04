"""Benchmark target repositories with ground truth expectations."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BenchmarkTarget:
    """A repository to benchmark ZEA against, with expected ground truth."""

    repo_url: str
    description: str
    expected_languages: list[str]
    expected_frameworks: list[str]
    expected_node_types: dict[str, int]  # {node_type: min_count}
    expected_has_tests: bool
    repo_name: str = ""

    def __post_init__(self) -> None:
        if not self.repo_name:
            self.repo_name = self.repo_url.rstrip("/").split("/")[-1]


BENCHMARK_TARGETS: list[BenchmarkTarget] = [
    BenchmarkTarget(
        repo_url="https://github.com/tiangolo/fastapi",
        description="FastAPI — Python async web framework. Tests REST API detection, Python inference.",
        expected_languages=["python"],
        expected_frameworks=["fastapi"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
            "rest_api": 1,
        },
        expected_has_tests=True,
    ),
    BenchmarkTarget(
        repo_url="https://github.com/django/django",
        description="Django — Python web framework monorepo. Tests Python detection and framework inference.",
        expected_languages=["python"],
        expected_frameworks=["django"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
        },
        expected_has_tests=True,
    ),
    BenchmarkTarget(
        repo_url="https://github.com/expressjs/express",
        description="Express.js — Node.js web framework. Tests JavaScript detection and framework inference.",
        expected_languages=["javascript"],
        expected_frameworks=["express"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
        },
        expected_has_tests=True,
    ),
    BenchmarkTarget(
        repo_url="https://github.com/nestjs/nest",
        description="NestJS — TypeScript Node.js framework. Tests TypeScript detection and NestJS inference.",
        expected_languages=["typescript"],
        expected_frameworks=["nestjs"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
        },
        expected_has_tests=True,
    ),
    BenchmarkTarget(
        repo_url="https://github.com/gothinkster/node-express-realworld-example-app",
        description="RealWorld Express app — Node.js/Express REST API with MongoDB. Tests full-stack detection.",
        expected_languages=["javascript"],
        expected_frameworks=["express"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
            "database": 1,
        },
        expected_has_tests=True,
        repo_name="node-express-realworld-example-app",
    ),
    BenchmarkTarget(
        repo_url="https://github.com/spring-projects/spring-petclinic",
        description="Spring PetClinic — Java/Spring Boot sample app. Tests Java and Spring inference.",
        expected_languages=["java"],
        expected_frameworks=["spring"],
        expected_node_types={
            "repository": 1,
            "backend": 1,
            "database": 1,
        },
        expected_has_tests=True,
    ),
]

# Lookup by URL
TARGETS_BY_URL: dict[str, BenchmarkTarget] = {t.repo_url: t for t in BENCHMARK_TARGETS}
