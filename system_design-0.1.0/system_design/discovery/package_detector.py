"""Detect package managers from manifest files."""
from __future__ import annotations

import json
from pathlib import Path

from system_design.discovery.models import PackageManager, PackageManagerDetection


def detect_package_managers(repo_path: Path) -> list[PackageManagerDetection]:
    detections: list[PackageManagerDetection] = []

    manifest_rules: list[tuple[str, PackageManager]] = [
        ("package-lock.json", PackageManager.NPM),
        ("package.json", PackageManager.NPM),      # fallback when no lock file
        ("yarn.lock", PackageManager.YARN),
        ("pnpm-lock.yaml", PackageManager.PNPM),
        ("requirements.txt", PackageManager.PIP),
        ("pyproject.toml", PackageManager.PIP),
        ("poetry.lock", PackageManager.POETRY),
        ("pdm.lock", PackageManager.PDM),
        ("Cargo.toml", PackageManager.CARGO),
        ("go.mod", PackageManager.GO_MOD),
        ("pom.xml", PackageManager.MAVEN),
        ("build.gradle", PackageManager.GRADLE),
        ("build.gradle.kts", PackageManager.GRADLE),
        ("Gemfile", PackageManager.BUNDLER),
    ]

    seen: set[PackageManager] = set()
    for filename, manager in manifest_rules:
        matches = list(repo_path.rglob(filename))
        for match in matches:
            if "node_modules" in str(match):
                continue
            if manager not in seen:
                deps: list[str] = []
                # Parse dependencies from common manifests
                if filename == "requirements.txt":
                    try:
                        lines = match.read_text(encoding="utf-8", errors="ignore").splitlines()
                        deps = [
                            l.strip().split("==")[0].split(">=")[0].strip()
                            for l in lines
                            if l.strip() and not l.startswith("#")
                        ][:20]
                    except Exception:
                        pass
                elif filename == "package.json":
                    try:
                        data = json.loads(match.read_text())
                        all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                        deps = list(all_deps.keys())[:20]
                    except Exception:
                        pass

                detections.append(PackageManagerDetection(
                    manager=manager,
                    manifest_file=str(match.relative_to(repo_path)),
                    dependencies=deps,
                ))
                seen.add(manager)

    return detections
