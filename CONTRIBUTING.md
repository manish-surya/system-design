# Contributing to ZEA

Thank you for your interest in contributing to ZEA. This document covers everything you need to go from zero to a merged pull request.

---

## Getting Started

### 1. Fork and clone

```bash
git clone https://github.com/YOUR_USERNAME/zea.git
cd zea
```

### 2. Install in development mode

```bash
pip install -e ".[dev]"
```

This installs ZEA plus all development dependencies: `pytest`, `pytest-cov`, `ruff`, `mypy`.

### 3. Verify the setup

```bash
pytest
zea --help
```

---

## Project Structure

```
zea/
├── zea/
│   ├── cli/           # Typer CLI entrypoints
│   ├── discovery/     # Milestone 1: Repository Discovery
│   ├── structural/    # Milestone 1.5: Structural Analysis
│   ├── graph/         # Milestone 2: AKG schema + builder
│   ├── inference/     # Milestone 3: Architecture Inference
│   ├── domain/        # Milestone 4: Domain Intelligence
│   ├── infrastructure/ # Milestone 5: Infrastructure Intelligence
│   ├── plugins/       # Plugin base classes + registry
│   └── core/          # Shared utilities (config, logging, evidence)
└── tests/
```

Each module owns exactly one pipeline stage. Keep it that way.

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=zea --cov-report=term-missing

# A specific module
pytest tests/discovery/

# A single test
pytest tests/graph/test_builder.py::test_node_creation
```

---

## Linting and Formatting

```bash
# Check for lint errors
ruff check zea/

# Auto-fix lint errors
ruff check zea/ --fix

# Format code
ruff format zea/

# Type checking
mypy zea/
```

CI enforces `ruff` lint passing. Format before you push.

---

## Adding a New Detector

Detectors live in `zea/inference/` and follow the plugin architecture. Here is the pattern:

### 1. Create the detector module

```python
# zea/inference/my_detector.py
from zea.plugins.base import BaseDetector
from zea.core.evidence import Evidence
from zea.graph.schema import Node

class MyDetector(BaseDetector):
    name = "my_detector"
    description = "Detects X from repository files"

    def detect(self, inventory) -> list[Node]:
        nodes = []
        for file in inventory.files:
            if self._matches(file):
                evidence = Evidence(
                    file_path=str(file.path),
                    pattern="my_pattern",
                    confidence=0.9,
                )
                node = Node(
                    id=f"my:{file.path.stem}",
                    type="MyType",
                    name=file.path.stem,
                    evidence=[evidence],
                )
                nodes.append(node)
        return nodes

    def _matches(self, file) -> bool:
        return file.path.suffix == ".myext"
```

### 2. Register the detector

```python
# zea/inference/engine.py  (add to the detector list)
from zea.inference.my_detector import MyDetector

DETECTORS = [
    ServiceDetector(),
    ApiDetector(),
    DatabaseDetector(),
    EventDetector(),
    MyDetector(),   # <-- add here
]
```

### 3. Write tests

```python
# tests/inference/test_my_detector.py
from zea.inference.my_detector import MyDetector

def test_my_detector_detects_x(fake_inventory):
    detector = MyDetector()
    nodes = detector.detect(fake_inventory)
    assert len(nodes) == 1
    assert nodes[0].type == "MyType"
    assert nodes[0].evidence[0].confidence == 0.9
```

### Rules for detectors

- Every node must include at least one `Evidence` object with a file path and confidence score.
- Detectors must not import from other detectors. Use shared utilities from `zea.core`.
- Confidence scores: `>= 0.9` for direct declaration (e.g., Dockerfile), `0.7–0.89` for strong pattern match, `0.5–0.69` for heuristic.

---

## Adding a New Language or Framework

Language detection lives in `zea/discovery/language_detector.py`. Framework detection is in `zea/discovery/framework_detector.py`. Both are driven by pattern tables — adding support is usually a one-liner.

---

## Pull Request Checklist

Before opening a PR, confirm:

- [ ] `pytest` passes with no failures
- [ ] `ruff check zea/` passes with no errors
- [ ] New code is type-annotated and `mypy zea/` passes
- [ ] New detectors include `Evidence` with confidence scores
- [ ] New public functions have docstrings
- [ ] Tests cover the happy path and at least one edge case
- [ ] The PR description explains *what* changed and *why*

---

## Opening an Issue

Use the issue templates:

- **Bug report** — `.github/ISSUE_TEMPLATE/bug_report.md`
- **Feature request** — `.github/ISSUE_TEMPLATE/feature_request.md`

---

## Code of Conduct

Be kind, be constructive. We review all PRs and aim to respond within 48 hours.
