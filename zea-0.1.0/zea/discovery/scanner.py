"""Top-level repository scanner — orchestrates all discovery detectors."""
from __future__ import annotations

import json
from pathlib import Path

from zea.core.config import ZEAConfig
from zea.core.logging import get_logger
from zea.discovery.doc_detector import detect_documentation
from zea.discovery.framework_detector import detect_frameworks
from zea.discovery.language_detector import detect_languages, primary_language
from zea.discovery.models import (
    InfrastructureDetection,
    InfrastructureType,
    RepositoryInventory,
)
from zea.discovery.package_detector import detect_package_managers

logger = get_logger(__name__)

_INFRA_PATTERNS: list[tuple[str, InfrastructureType]] = [
    ("Dockerfile", InfrastructureType.DOCKER),
    ("docker-compose*.yml", InfrastructureType.DOCKER_COMPOSE),
    ("docker-compose*.yaml", InfrastructureType.DOCKER_COMPOSE),
    ("*.tf", InfrastructureType.TERRAFORM),
    ("Chart.yaml", InfrastructureType.HELM),
    ("values.yaml", InfrastructureType.HELM),
    (".github/workflows/*.yml", InfrastructureType.GITHUB_ACTIONS),
    (".gitlab-ci.yml", InfrastructureType.GITLAB_CI),
    (".circleci/config.yml", InfrastructureType.CIRCLE_CI),
]

_K8S_PATTERNS = ["*.yaml", "*.yml"]
_K8S_KEYWORDS = {"kind: Deployment", "kind: Service", "kind: Pod", "kind: Ingress"}


def _collect_files(repo_path: Path, config: ZEAConfig) -> list[Path]:
    """Walk the repo, skipping excluded dirs, and collect all files."""
    exclude = set(config.exclude_dirs)
    files: list[Path] = []

    def walk(path: Path) -> None:
        try:
            for entry in path.iterdir():
                if entry.is_dir():
                    if entry.name not in exclude and not entry.name.endswith(".egg-info"):
                        walk(entry)
                elif entry.is_file():
                    try:
                        if entry.stat().st_size <= config.max_file_size_kb * 1024:
                            files.append(entry)
                    except OSError:
                        pass
        except PermissionError:
            pass

    walk(repo_path)
    return files


def _detect_infrastructure(repo_path: Path) -> list[InfrastructureDetection]:
    seen: dict[InfrastructureType, list[str]] = {}

    for pattern, infra_type in _INFRA_PATTERNS:
        for f in repo_path.rglob(pattern):
            if "node_modules" in str(f):
                continue
            rel = str(f.relative_to(repo_path))
            seen.setdefault(infra_type, []).append(rel)

    # Kubernetes YAML detection (heuristic: YAML with k8s kind keywords)
    for pattern in _K8S_PATTERNS:
        for f in repo_path.rglob(pattern):
            if "node_modules" in str(f) or ".github" in str(f):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if any(kw in content for kw in _K8S_KEYWORDS):
                    rel = str(f.relative_to(repo_path))
                    seen.setdefault(InfrastructureType.KUBERNETES, []).append(rel)
            except Exception:
                pass

    return [
        InfrastructureDetection(type=infra_type, files=files[:10])
        for infra_type, files in seen.items()
    ]


def _has_tests(repo_path: Path) -> bool:
    test_indicators = ["tests/", "test/", "__tests__/", "spec/", "*.test.*", "*.spec.*"]
    for indicator in test_indicators[:4]:
        if list(repo_path.rglob(indicator))[:1]:
            return True
    return any(
        f for f in repo_path.rglob("*.py")
        if f.name.startswith("test_") or f.name.endswith("_test.py")
    )


def _has_ci(infra: list[InfrastructureDetection]) -> bool:
    ci_types = {InfrastructureType.GITHUB_ACTIONS, InfrastructureType.GITLAB_CI, InfrastructureType.CIRCLE_CI}
    return any(i.type in ci_types for i in infra)


def scan_repository(repo_path: Path, config: ZEAConfig | None = None) -> RepositoryInventory:
    """
    Entry point for Milestone 1 — Repository Discovery.

    Returns a RepositoryInventory with languages, frameworks,
    package managers, infrastructure, and documentation.
    """
    config = config or ZEAConfig()
    repo_path = repo_path.resolve()

    logger.info(f"Scanning repository: {repo_path}")

    files = _collect_files(repo_path, config)
    logger.debug(f"Found {len(files)} files")

    lang_stats = detect_languages(files)
    frameworks = detect_frameworks(repo_path)
    pkg_managers = detect_package_managers(repo_path)
    infrastructure = _detect_infrastructure(repo_path)
    documentation = detect_documentation(repo_path)

    dirs = sum(1 for _ in repo_path.rglob("*") if _.is_dir())

    inventory = RepositoryInventory(
        repository_path=str(repo_path),
        repository_name=repo_path.name,
        languages=lang_stats,
        primary_language=primary_language(lang_stats),
        frameworks=frameworks,
        package_managers=pkg_managers,
        infrastructure=infrastructure,
        documentation=documentation,
        total_files=len(files),
        total_directories=dirs,
        has_tests=_has_tests(repo_path),
        has_ci=_has_ci(infrastructure),
    )

    logger.info(
        f"Discovery complete: {len(lang_stats)} languages, "
        f"{len(frameworks)} frameworks, "
        f"{len(pkg_managers)} package managers"
    )
    return inventory


def save_inventory(inventory: RepositoryInventory, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(inventory.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    logger.info(f"Saved repository_inventory.json → {output_path}")
