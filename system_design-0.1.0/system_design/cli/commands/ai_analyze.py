"""system-design ai-analyze — AI-powered architecture analysis using Claude."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def ai_analyze_command(
    repo_path: Path,
    output_dir: Path,
    model: str,
    verbose: bool,
) -> None:
    """
    Full pipeline:
    1. Static scan  →  repository_inventory.json + architecture_graph.json
    2. Claude AI    →  architecture.json + architecture.md + service-map.json + domain-map.json
    3. 3D render    →  architecture.html
    """
    from system_design.core.config import ZEAConfig
    from system_design.core.logging import setup_logging
    from system_design.discovery.scanner import save_inventory, scan_repository
    from system_design.graph.builder import AKGBuilder
    from system_design.graph.serializer import save_graph
    from system_design.inference.engine import InferenceEngine
    from system_design.ai.analyzer import analyze_with_claude, save_analysis
    from system_design.visualization.threejs_generator import generate_html

    setup_logging(verbose)
    if not repo_path.exists():
        console.print(f"[red]Error:[/red] Path not found: {repo_path}")
        raise typer.Exit(1)

    config = ZEAConfig(output_dir=output_dir, verbose=verbose)
    console.print(f"\n[bold blue]system-design[/bold blue] AI Analysis — [cyan]{repo_path.resolve().name}[/cyan]\n")

    # ── Stage 1: Static discovery ──────────────────────────────────────────────
    with console.status("[bold]Stage 1/4:[/bold] Scanning repository…"):
        inventory = scan_repository(repo_path, config)
        save_inventory(inventory, config.output_path("repository_inventory.json"))

    console.print(
        f"  [green]✓[/green] Discovery: [b]{len(inventory.languages)}[/b] languages, "
        f"[b]{len(inventory.frameworks)}[/b] frameworks, "
        f"[b]{inventory.total_files}[/b] files"
    )

    # ── Stage 2: Static graph ──────────────────────────────────────────────────
    with console.status("[bold]Stage 2/4:[/bold] Building knowledge graph…"):
        builder = AKGBuilder(inventory)
        akg = builder.build()
        engine = InferenceEngine(akg, repo_path)
        akg = engine.run()
        save_graph(akg, config.output_path("architecture_graph.json"))

    console.print(
        f"  [green]✓[/green] Graph: [b]{akg.node_count}[/b] nodes, [b]{akg.edge_count}[/b] edges"
    )

    # ── Stage 3: AI analysis ───────────────────────────────────────────────────
    with console.status("[bold]Stage 3/4:[/bold] AI architecture analysis (Claude)…"):
        inventory_dict = json.loads(
            config.output_path("repository_inventory.json").read_text()
        )
        graph_dict = json.loads(
            config.output_path("architecture_graph.json").read_text()
        )
        analysis = analyze_with_claude(inventory_dict, graph_dict, model=model)
        analysis["_repo_name"] = inventory.repository_name
        outputs = save_analysis(analysis, output_dir)

    console.print(
        f"  [green]✓[/green] AI analysis: [b]{len(analysis.get('components',[]))}[/b] components, "
        f"[b]{len(analysis.get('connections',[]))}[/b] connections, "
        f"[b]{len(analysis.get('domains',[]))}[/b] domains"
    )

    # ── Stage 4: 3D render ─────────────────────────────────────────────────────
    with console.status("[bold]Stage 4/4:[/bold] Rendering 3D system design…"):
        html_path = config.output_path("architecture.html")
        generate_html(analysis, html_path)

    console.print(f"  [green]✓[/green] 3D system design rendered\n")

    # ── Summary ────────────────────────────────────────────────────────────────
    console.print(f"[bold green]✓[/bold green] Complete. Artifacts in [cyan]{output_dir}[/cyan]:\n")
    files = [
        ("repository_inventory.json", "Static discovery"),
        ("architecture_graph.json",   "Knowledge graph"),
        ("architecture.json",         "AI architecture analysis"),
        ("architecture.md",           "System design document"),
        ("service-map.json",          "Service dependency map"),
        ("domain-map.json",           "Domain map"),
        ("architecture.html",         "3D interactive system design"),
    ]
    for fname, desc in files:
        p = output_dir / fname
        if p.exists():
            console.print(f"  [dim]{fname:35}[/dim] {desc}")

    console.print(f"\n  [bold]Open:[/bold] {output_dir / 'architecture.html'}\n")
