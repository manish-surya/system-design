"""
Smoke test for the ZEA benchmark suite.

Creates a minimal fake Python/FastAPI repo in a temp directory,
runs ZEA discovery + inference on it, and asserts that:
  1. The primary language is detected as Python.
  2. The AKG has at least one node.
  3. Inventory scoring functions return valid dicts.
  4. Graph scoring functions return valid dicts.

No network access required — runs entirely offline.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from tests.benchmark.metrics import combined_score, score_graph, score_inventory
from tests.benchmark.targets import BenchmarkTarget


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_fastapi_repo(base: Path) -> Path:
    """Write a minimal Python/FastAPI repo structure under base/."""
    repo = base / "fake_fastapi_app"
    repo.mkdir()

    # requirements.txt signals FastAPI dependency
    (repo / "requirements.txt").write_text(
        "fastapi>=0.100.0\nuvicorn>=0.22.0\npydantic>=2.0\n",
        encoding="utf-8",
    )

    # main.py — simple FastAPI app
    (repo / "main.py").write_text(
        """from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


@app.post("/items")
def create_item(name: str):
    return {"name": name}
""",
        encoding="utf-8",
    )

    # tests/ directory so has_tests is True
    tests_dir = repo / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("", encoding="utf-8")
    (tests_dir / "test_main.py").write_text(
        """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
""",
        encoding="utf-8",
    )

    # Minimal README
    (repo / "README.md").write_text("# Fake FastAPI App\n", encoding="utf-8")

    return repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSmokeZEAOnFakeRepo:
    """Run ZEA on a synthetic repo and verify basic correctness."""

    @pytest.fixture(scope="class")
    def fake_repo(self, tmp_path_factory: pytest.TempPathFactory) -> Path:
        base = tmp_path_factory.mktemp("benchmark_smoke")
        return _make_fake_fastapi_repo(base)

    @pytest.fixture(scope="class")
    def inventory_and_graph(self, fake_repo: Path):
        """Run ZEA discovery + inference, return (inventory_dict, graph_dict)."""
        from zea.core.config import ZEAConfig
        from zea.discovery.scanner import scan_repository
        from zea.graph.builder import AKGBuilder
        from zea.inference.engine import InferenceEngine

        config = ZEAConfig()
        inventory = scan_repository(fake_repo, config)
        inventory_dict = json.loads(json.dumps(inventory.model_dump(), default=str))

        builder = AKGBuilder(inventory)
        akg = builder.build()

        engine = InferenceEngine(akg, fake_repo)
        akg = engine.run()

        graph_dict = json.loads(akg.model_dump_json())
        return inventory_dict, graph_dict

    # -- Inventory assertions --

    def test_primary_language_is_python(self, inventory_and_graph):
        inventory_dict, _ = inventory_and_graph
        primary = inventory_dict.get("primary_language", "")
        assert primary == "python", (
            f"Expected primary_language='python', got '{primary}'. "
            f"Detected languages: {inventory_dict.get('languages', [])}"
        )

    def test_fastapi_framework_detected(self, inventory_and_graph):
        inventory_dict, _ = inventory_and_graph
        frameworks = [fd["framework"] for fd in inventory_dict.get("frameworks", [])]
        assert "fastapi" in frameworks, (
            f"Expected 'fastapi' in detected frameworks, got: {frameworks}"
        )

    def test_has_tests_is_true(self, inventory_and_graph):
        inventory_dict, _ = inventory_and_graph
        assert inventory_dict.get("has_tests") is True, (
            "Expected has_tests=True for repo with tests/ directory"
        )

    # -- Graph assertions --

    def test_graph_has_at_least_one_node(self, inventory_and_graph):
        _, graph_dict = inventory_and_graph
        nodes = graph_dict.get("nodes", [])
        assert len(nodes) >= 1, "Expected at least 1 node in the AKG"

    def test_graph_has_repository_node(self, inventory_and_graph):
        _, graph_dict = inventory_and_graph
        node_types = [n.get("type") for n in graph_dict.get("nodes", [])]
        assert "repository" in node_types, (
            f"Expected a 'repository' node; found types: {node_types}"
        )

    def test_graph_has_backend_node(self, inventory_and_graph):
        _, graph_dict = inventory_and_graph
        node_types = [n.get("type") for n in graph_dict.get("nodes", [])]
        assert "backend" in node_types, (
            f"Expected a 'backend' node (FastAPI detected); found types: {node_types}"
        )

    # -- Metrics / scoring assertions --

    def test_score_inventory_returns_valid_dict(self, inventory_and_graph):
        inventory_dict, _ = inventory_and_graph
        target = BenchmarkTarget(
            repo_url="https://example.com/fake",
            description="Fake FastAPI repo",
            expected_languages=["python"],
            expected_frameworks=["fastapi"],
            expected_node_types={"repository": 1, "backend": 1},
            expected_has_tests=True,
            repo_name="fake_fastapi_app",
        )
        scores = score_inventory(inventory_dict, target)
        assert isinstance(scores, dict)
        assert "language_f1" in scores
        assert "framework_f1" in scores
        assert "inventory_overall" in scores
        assert scores["language_f1"] == 1.0, (
            f"Expected perfect language F1; got {scores['language_f1']}"
        )
        assert scores["framework_f1"] == 1.0, (
            f"Expected perfect framework F1; got {scores['framework_f1']}"
        )

    def test_score_graph_returns_valid_dict(self, inventory_and_graph):
        _, graph_dict = inventory_and_graph
        target = BenchmarkTarget(
            repo_url="https://example.com/fake",
            description="Fake FastAPI repo",
            expected_languages=["python"],
            expected_frameworks=["fastapi"],
            expected_node_types={"repository": 1, "backend": 1},
            expected_has_tests=True,
            repo_name="fake_fastapi_app",
        )
        scores = score_graph(graph_dict, target)
        assert isinstance(scores, dict)
        assert "node_type_scores" in scores
        assert "graph_overall" in scores
        assert scores["graph_overall"] == 1.0, (
            f"Expected all node type requirements met; got {scores}"
        )

    def test_combined_score_in_range(self, inventory_and_graph):
        inventory_dict, graph_dict = inventory_and_graph
        target = BenchmarkTarget(
            repo_url="https://example.com/fake",
            description="Fake FastAPI repo",
            expected_languages=["python"],
            expected_frameworks=["fastapi"],
            expected_node_types={"repository": 1, "backend": 1},
            expected_has_tests=True,
            repo_name="fake_fastapi_app",
        )
        inv_scores = score_inventory(inventory_dict, target)
        grph_scores = score_graph(graph_dict, target)
        score = combined_score(inv_scores, grph_scores)
        assert 0.0 <= score <= 1.0, f"Combined score out of range: {score}"
        assert score >= 0.85, (
            f"Expected excellent score (>=0.85) for perfect fake repo; got {score}"
        )


# ---------------------------------------------------------------------------
# Standalone metric unit tests
# ---------------------------------------------------------------------------

class TestMetricFunctions:
    """Unit tests for precision/recall/f1 — no ZEA dependency."""

    def test_precision_all_correct(self):
        from tests.benchmark.metrics import precision
        assert precision(["python", "javascript"], ["python", "javascript"]) == 1.0

    def test_precision_none_correct(self):
        from tests.benchmark.metrics import precision
        assert precision(["java"], ["python"]) == 0.0

    def test_precision_partial(self):
        from tests.benchmark.metrics import precision
        assert precision(["python", "java"], ["python"]) == 0.5

    def test_recall_all_found(self):
        from tests.benchmark.metrics import recall
        assert recall(["python", "javascript"], ["python"]) == 1.0

    def test_recall_none_found(self):
        from tests.benchmark.metrics import recall
        assert recall([], ["python"]) == 0.0

    def test_recall_empty_expected(self):
        from tests.benchmark.metrics import recall
        assert recall(["python"], []) == 1.0

    def test_f1_perfect(self):
        from tests.benchmark.metrics import f1
        assert f1(1.0, 1.0) == 1.0

    def test_f1_zero(self):
        from tests.benchmark.metrics import f1
        assert f1(0.0, 0.0) == 0.0

    def test_f1_harmonic(self):
        from tests.benchmark.metrics import f1
        result = f1(0.5, 1.0)
        assert abs(result - (2 * 0.5 * 1.0 / 1.5)) < 1e-9
