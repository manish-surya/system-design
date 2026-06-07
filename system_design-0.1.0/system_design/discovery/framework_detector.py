"""Detect frameworks from package manifests and file patterns."""
from __future__ import annotations

import json
import re
from pathlib import Path

from system_design.discovery.models import Framework, FrameworkDetection


def _check_package_json(repo_path: Path) -> list[FrameworkDetection]:
    detections: list[FrameworkDetection] = []
    pkg_files = list(repo_path.rglob("package.json"))

    # Collect all deps across package.json files
    all_deps: set[str] = set()
    for pkg_file in pkg_files:
        if "node_modules" in str(pkg_file):
            continue
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8", errors="ignore"))
            deps = {
                **data.get("dependencies", {}),
                **data.get("devDependencies", {}),
            }
            all_deps.update(deps.keys())
        except Exception:
            continue

    rules: list[tuple[str, Framework, float]] = [
        ("next", Framework.NEXTJS, 0.95),
        ("react", Framework.REACT, 0.9),
        ("@angular/core", Framework.ANGULAR, 0.95),
        ("vue", Framework.VUE, 0.9),
        ("express", Framework.EXPRESS, 0.9),
        ("@nestjs/core", Framework.NESTJS, 0.95),
    ]
    for dep, framework, conf in rules:
        if dep in all_deps:
            detections.append(FrameworkDetection(
                framework=framework,
                confidence=conf,
                evidence=[f"Found '{dep}' in package.json dependencies"],
            ))
    return detections


def _check_requirements(repo_path: Path) -> list[FrameworkDetection]:
    detections: list[FrameworkDetection] = []
    req_files = (
        list(repo_path.rglob("requirements*.txt"))
        + list(repo_path.rglob("pyproject.toml"))
        + list(repo_path.rglob("setup.py"))
        + list(repo_path.rglob("setup.cfg"))
        + list(repo_path.rglob("Pipfile"))
    )

    content = ""
    for f in req_files:
        try:
            content += f.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue

    rules: list[tuple[str, Framework, float]] = [
        ("fastapi", Framework.FASTAPI, 0.95),
        ("django", Framework.DJANGO, 0.95),
        ("flask", Framework.FLASK, 0.9),
    ]
    for keyword, framework, conf in rules:
        if re.search(rf"\b{keyword}\b", content):
            detections.append(FrameworkDetection(
                framework=framework,
                confidence=conf,
                evidence=[f"Found '{keyword}' in Python dependency files"],
            ))
    return detections


def _check_go_mod(repo_path: Path) -> list[FrameworkDetection]:
    detections: list[FrameworkDetection] = []
    go_mods = list(repo_path.rglob("go.mod"))
    content = ""
    for f in go_mods:
        try:
            content += f.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue

    rules: list[tuple[str, Framework, float]] = [
        ("gin-gonic/gin", Framework.GIN, 0.95),
        ("labstack/echo", Framework.ECHO, 0.95),
        ("gofiber/fiber", Framework.FIBER, 0.95),
    ]
    for keyword, framework, conf in rules:
        if keyword in content:
            detections.append(FrameworkDetection(
                framework=framework,
                confidence=conf,
                evidence=[f"Found '{keyword}' in go.mod"],
            ))
    return detections


def _check_java(repo_path: Path) -> list[FrameworkDetection]:
    detections: list[FrameworkDetection] = []
    build_files = list(repo_path.rglob("pom.xml")) + list(repo_path.rglob("build.gradle*"))
    content = ""
    for f in build_files:
        try:
            content += f.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
    if "spring" in content or "springframework" in content:
        detections.append(FrameworkDetection(
            framework=Framework.SPRING,
            confidence=0.95,
            evidence=["Found 'spring' in pom.xml/build.gradle"],
        ))
    return detections


def detect_frameworks(repo_path: Path) -> list[FrameworkDetection]:
    """Detect frameworks from all package manifest files."""
    detections: list[FrameworkDetection] = []
    detections.extend(_check_package_json(repo_path))
    detections.extend(_check_requirements(repo_path))
    detections.extend(_check_go_mod(repo_path))
    detections.extend(_check_java(repo_path))
    return detections
