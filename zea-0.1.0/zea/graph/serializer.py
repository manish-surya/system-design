"""Serialize/deserialize ArchitectureKnowledgeGraph to/from JSON."""
from __future__ import annotations

import json
from pathlib import Path

from zea.core.logging import get_logger
from zea.graph.schema import ArchitectureKnowledgeGraph

logger = get_logger(__name__)


def save_graph(akg: ArchitectureKnowledgeGraph, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(akg.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    logger.info(f"Saved architecture_graph.json → {output_path}")


def load_graph(path: Path) -> ArchitectureKnowledgeGraph:
    data = json.loads(path.read_text(encoding="utf-8"))
    return ArchitectureKnowledgeGraph.model_validate(data)
