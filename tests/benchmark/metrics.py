"""Scoring functions for ZEA benchmark evaluation."""
from __future__ import annotations

from typing import Any

from tests.benchmark.targets import BenchmarkTarget


def precision(detected: list[str], expected: list[str]) -> float:
    """Fraction of detected items that are correct (in expected)."""
    if not detected:
        return 0.0
    expected_set = {e.lower() for e in expected}
    correct = sum(1 for d in detected if d.lower() in expected_set)
    return correct / len(detected)


def recall(detected: list[str], expected: list[str]) -> float:
    """Fraction of expected items that were actually detected."""
    if not expected:
        return 1.0  # nothing expected, nothing to miss
    detected_set = {d.lower() for d in detected}
    found = sum(1 for e in expected if e.lower() in detected_set)
    return found / len(expected)


def f1(prec: float, rec: float) -> float:
    """Harmonic mean of precision and recall."""
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def score_inventory(inventory_dict: dict[str, Any], target: BenchmarkTarget) -> dict[str, Any]:
    """
    Score a repository_inventory.json dict against ground truth.

    Returns a dict with:
      - language_precision, language_recall, language_f1
      - framework_precision, framework_recall, framework_f1
      - has_tests_correct: bool
      - overall: average of language_f1, framework_f1, tests_score
    """
    # Extract detected languages
    detected_languages = [
        ls["language"] for ls in inventory_dict.get("languages", [])
    ]

    # Extract detected frameworks
    detected_frameworks = [
        fd["framework"] for fd in inventory_dict.get("frameworks", [])
    ]

    has_tests = inventory_dict.get("has_tests", False)
    tests_correct = has_tests == target.expected_has_tests

    lang_prec = precision(detected_languages, target.expected_languages)
    lang_rec = recall(detected_languages, target.expected_languages)
    lang_f1 = f1(lang_prec, lang_rec)

    fw_prec = precision(detected_frameworks, target.expected_frameworks)
    fw_rec = recall(detected_frameworks, target.expected_frameworks)
    fw_f1 = f1(fw_prec, fw_rec)

    tests_score = 1.0 if tests_correct else 0.0

    overall = (lang_f1 + fw_f1 + tests_score) / 3.0

    return {
        "language_precision": round(lang_prec, 3),
        "language_recall": round(lang_rec, 3),
        "language_f1": round(lang_f1, 3),
        "framework_precision": round(fw_prec, 3),
        "framework_recall": round(fw_rec, 3),
        "framework_f1": round(fw_f1, 3),
        "has_tests_correct": tests_correct,
        "tests_score": round(tests_score, 3),
        "inventory_overall": round(overall, 3),
        "detected_languages": detected_languages,
        "detected_frameworks": detected_frameworks,
    }


def score_graph(graph_dict: dict[str, Any], target: BenchmarkTarget) -> dict[str, Any]:
    """
    Score an architecture_graph.json dict against ground truth.

    Checks that each expected node type appears at least min_count times.

    Returns a dict with:
      - node_type_scores: {node_type: {"expected_min": n, "detected": n, "met": bool}}
      - node_types_met: fraction of requirements met
      - graph_overall: same as node_types_met (the primary graph metric)
    """
    nodes = graph_dict.get("nodes", [])

    # Count nodes by type
    detected_counts: dict[str, int] = {}
    for node in nodes:
        ntype = node.get("type", "unknown")
        detected_counts[ntype] = detected_counts.get(ntype, 0) + 1

    node_type_scores: dict[str, dict[str, Any]] = {}
    requirements_met = 0
    total_requirements = len(target.expected_node_types)

    for node_type, min_count in target.expected_node_types.items():
        detected = detected_counts.get(node_type, 0)
        met = detected >= min_count
        if met:
            requirements_met += 1
        node_type_scores[node_type] = {
            "expected_min": min_count,
            "detected": detected,
            "met": met,
        }

    node_types_fraction = requirements_met / total_requirements if total_requirements > 0 else 1.0

    return {
        "node_type_scores": node_type_scores,
        "node_types_met": round(node_types_fraction, 3),
        "graph_overall": round(node_types_fraction, 3),
        "total_nodes_detected": len(nodes),
        "detected_type_counts": detected_counts,
    }


def combined_score(inventory_scores: dict[str, Any], graph_scores: dict[str, Any]) -> float:
    """Weighted overall score combining inventory and graph metrics."""
    inv = inventory_scores.get("inventory_overall", 0.0)
    grp = graph_scores.get("graph_overall", 0.0)
    # Equal weight: inventory (language + framework + tests) and graph (node types)
    return round((inv + grp) / 2.0, 3)
