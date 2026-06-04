"""Detect documentation artifacts in a repository."""
from __future__ import annotations

import re
from pathlib import Path

from zea.discovery.models import DocumentationDetection, DocumentationType


def detect_documentation(repo_path: Path) -> list[DocumentationDetection]:
    detections: list[DocumentationDetection] = []

    # README
    for readme in repo_path.rglob("README*"):
        detections.append(DocumentationDetection(
            type=DocumentationType.README,
            path=str(readme.relative_to(repo_path)),
        ))
        break  # Just the root README

    # OpenAPI specs
    for pattern in ["openapi*.yaml", "openapi*.json", "swagger*.yaml", "swagger*.json", "api*.yaml"]:
        for f in repo_path.rglob(pattern):
            if "node_modules" in str(f):
                continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "openapi" in content.lower() or "swagger" in content.lower():
                    detections.append(DocumentationDetection(
                        type=DocumentationType.OPENAPI,
                        path=str(f.relative_to(repo_path)),
                    ))
            except Exception:
                pass

    # AsyncAPI
    for f in repo_path.rglob("asyncapi*.yaml"):
        detections.append(DocumentationDetection(
            type=DocumentationType.ASYNCAPI,
            path=str(f.relative_to(repo_path)),
        ))

    # ADRs
    adr_dirs = ["docs/adr", "adr", "decisions", "doc/adr", "docs/decisions"]
    for adr_dir in adr_dirs:
        adr_path = repo_path / adr_dir
        if adr_path.exists():
            for f in adr_path.iterdir():
                if f.suffix in {".md", ".txt"}:
                    detections.append(DocumentationDetection(
                        type=DocumentationType.ADR,
                        path=str(f.relative_to(repo_path)),
                    ))
            break

    # Architecture docs (heuristic: files in docs/ with architecture-related names)
    arch_patterns = re.compile(r"architect|system.design|component|infrastructure", re.IGNORECASE)
    for f in repo_path.rglob("*.md"):
        if "node_modules" in str(f) or f.name.upper().startswith("README"):
            continue
        if arch_patterns.search(f.stem):
            detections.append(DocumentationDetection(
                type=DocumentationType.ARCHITECTURE_DOC,
                path=str(f.relative_to(repo_path)),
            ))

    return detections
