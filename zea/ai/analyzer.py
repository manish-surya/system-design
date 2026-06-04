"""
ZEA AI Architecture Analyzer
=============================
Uses Claude to analyze a repository inventory + static graph and produce
a rich structured architecture description for 3D rendering.

Requires: ANTHROPIC_API_KEY environment variable.
Falls back gracefully to static inference if API key not set.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from zea.ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from zea.core.logging import get_logger

logger = get_logger(__name__)

_MAX_NODES_IN_PROMPT = 60  # truncate to keep token count manageable
_MAX_EDGES_IN_PROMPT = 80


def _summarize_nodes(nodes: list[dict]) -> str:
    lines = []
    for n in nodes[:_MAX_NODES_IN_PROMPT]:
        lines.append(f"  - [{n.get('type','?')}] id={n.get('id','?')}  name={n.get('name','?')}")
    if len(nodes) > _MAX_NODES_IN_PROMPT:
        lines.append(f"  ... and {len(nodes) - _MAX_NODES_IN_PROMPT} more")
    return "\n".join(lines)


def _summarize_edges(edges: list[dict]) -> str:
    lines = []
    for e in edges[:_MAX_EDGES_IN_PROMPT]:
        lines.append(
            f"  - {e.get('source_id','?')} --[{e.get('type','?')}]--> {e.get('target_id','?')}"
        )
    if len(edges) > _MAX_EDGES_IN_PROMPT:
        lines.append(f"  ... and {len(edges) - _MAX_EDGES_IN_PROMPT} more")
    return "\n".join(lines)


def _build_prompt(inventory: dict, graph: dict) -> str:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    inv   = inventory

    return USER_PROMPT_TEMPLATE.format(
        repo_name       = inv.get("repository_name", "unknown"),
        primary_language= inv.get("primary_language", "unknown"),
        languages       = ", ".join(
            f"{l['language']}({l['file_count']} files)"
            for l in inv.get("languages", [])
        ) or "none detected",
        frameworks      = ", ".join(
            f['framework'] for f in inv.get("frameworks", [])
        ) or "none detected",
        package_managers= ", ".join(
            p['manager'] for p in inv.get("package_managers", [])
        ) or "none",
        infrastructure  = ", ".join(
            i['type'] for i in inv.get("infrastructure", [])
        ) or "none detected",
        has_tests       = inv.get("has_tests", False),
        has_ci          = inv.get("has_ci", False),
        total_files     = inv.get("total_files", 0),
        node_count      = len(nodes),
        nodes_summary   = _summarize_nodes(nodes),
        edge_count      = len(edges),
        edges_summary   = _summarize_edges(edges),
    )


def _extract_json(text: str) -> dict:
    """Extract JSON from Claude's response (handles markdown code blocks)."""
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Find the first { ... } block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not extract valid JSON from Claude response")


def _static_fallback(inventory: dict, graph: dict) -> dict:
    """Generate a minimal architecture analysis without Claude."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    repo  = inventory.get("repository_name", "system")

    LAYER_MAP = {
        "frontend": "frontend", "backend": "service", "monolith": "service",
        "service": "service", "gateway": "gateway", "worker": "service",
        "database": "data", "cache": "data",
        "queue": "messaging", "topic": "messaging", "event": "messaging",
        "rest_api": "gateway", "graphql_api": "gateway", "grpc_api": "gateway",
        "webhook": "gateway", "cluster": "infrastructure", "namespace": "infrastructure",
        "pod": "infrastructure", "external_system": "external",
        "domain": "service", "repository": "service", "team": "external",
    }
    SHAPE_MAP = {
        "frontend": "cuboid", "backend": "cube", "monolith": "cube",
        "service": "cube", "gateway": "cuboid", "worker": "cuboid",
        "database": "cylinder", "cache": "cylinder",
        "queue": "torus", "topic": "torus", "event": "octahedron",
        "rest_api": "panel", "graphql_api": "panel", "grpc_api": "panel",
        "cluster": "cuboid", "external_system": "sphere", "domain": "cuboid",
    }
    WIRELESS_TYPES = {"PUBLISHES", "CONSUMES", "INVOKES"}

    components = []
    for n in nodes:
        ntype = n.get("type", "unknown")
        components.append({
            "node_id":      n.get("id", ""),
            "display_name": n.get("name", n.get("id", "")),
            "description":  f"A {ntype} component in {repo}",
            "capabilities": [],
            "layer":        LAYER_MAP.get(ntype, "service"),
            "shape":        SHAPE_MAP.get(ntype, "cube"),
            "importance":   3,
        })

    connections = []
    for e in edges:
        etype = e.get("type", "CALLS")
        connections.append({
            "source_id": e.get("source_id", ""),
            "target_id": e.get("target_id", ""),
            "edge_type":  etype,
            "wire_type":  "wireless" if etype in WIRELESS_TYPES else "wired",
            "label":      etype.lower().replace("_", " "),
        })

    return {
        "system_description": f"Software system: {repo}",
        "system_type":        "unknown",
        "components":         components,
        "connections":        connections,
        "domains":            [],
    }


def analyze_with_claude(
    inventory: dict,
    graph: dict,
    model: str = "claude-opus-4-6",
) -> dict:
    """
    Send repository inventory + graph to Claude and return structured
    architecture analysis.

    Returns a dict with keys: system_description, system_type,
    components, connections, domains.

    If ANTHROPIC_API_KEY is not set, falls back to static analysis.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning(
            "ANTHROPIC_API_KEY not set — using static fallback analysis. "
            "Set the key to enable AI-powered architecture analysis."
        )
        return _static_fallback(inventory, graph)

    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed. Run: pip install anthropic")
        return _static_fallback(inventory, graph)

    logger.info(f"Sending repository to Claude ({model}) for architecture analysis...")

    prompt = _build_prompt(inventory, graph)
    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text
        result = _extract_json(raw)
        logger.info(
            f"AI analysis complete: {len(result.get('components', []))} components, "
            f"{len(result.get('connections', []))} connections, "
            f"{len(result.get('domains', []))} domains"
        )
        return result
    except Exception as e:
        logger.warning(f"Claude API call failed ({e}) — using static fallback")
        return _static_fallback(inventory, graph)


def save_analysis(analysis: dict, output_dir: Path) -> dict[str, Path]:
    """Save AI analysis as separate output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    # architecture.json (enriched graph)
    arch_path = output_dir / "architecture.json"
    arch_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    outputs["architecture"] = arch_path

    # service-map.json
    services = [
        c for c in analysis.get("components", [])
        if c.get("layer") in {"service", "gateway", "frontend"}
    ]
    sm_path = output_dir / "service-map.json"
    sm_path.write_text(json.dumps({
        "services": services,
        "connections": [
            c for c in analysis.get("connections", [])
            if c.get("edge_type") in {"CALLS", "DEPENDS_ON"}
        ],
    }, indent=2), encoding="utf-8")
    outputs["service_map"] = sm_path

    # domain-map.json
    dm_path = output_dir / "domain-map.json"
    dm_path.write_text(json.dumps({
        "domains": analysis.get("domains", []),
    }, indent=2), encoding="utf-8")
    outputs["domain_map"] = dm_path

    # architecture.md
    md_lines = [
        f"# {analysis.get('system_description', 'Architecture')}",
        f"\n**System Type:** {analysis.get('system_type', 'unknown')}\n",
        "\n## Components\n",
    ]
    for c in analysis.get("components", []):
        md_lines.append(f"### {c['display_name']} `[{c.get('layer','?')}]`")
        md_lines.append(f"{c.get('description', '')}")
        caps = c.get("capabilities", [])
        if caps:
            md_lines.append("\n**Capabilities:**")
            for cap in caps:
                md_lines.append(f"- {cap}")
        md_lines.append("")

    if analysis.get("domains"):
        md_lines.append("\n## Domains\n")
        for d in analysis["domains"]:
            md_lines.append(f"### {d['name']}")
            md_lines.append(d.get("description", ""))
            md_lines.append("")

    md_path = output_dir / "architecture.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    outputs["architecture_md"] = md_path

    logger.info(f"Saved analysis artifacts to {output_dir}")
    return outputs
