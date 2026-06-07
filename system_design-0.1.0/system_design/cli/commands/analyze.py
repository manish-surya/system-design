"""system-design analyze — full pipeline: Discovery → Graph → Inference."""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

# Default output directory
_DEFAULT_OUTPUT = Path(".system-design")

from system_design.core.config import ZEAConfig
from system_design.core.logging import setup_logging
from system_design.discovery.scanner import save_inventory, scan_repository
from system_design.graph.builder import AKGBuilder
from system_design.graph.serializer import save_graph
from system_design.inference.engine import InferenceEngine

console = Console()


def analyze_command(
    repo_path: Path,
    output_dir: Path = Path(".system-design"),
    verbose: bool = False,
    skip_inference: bool = False,
) -> None:
    """Analyze a repository and generate the Architecture Knowledge Graph."""
    setup_logging(verbose)

    if not repo_path.exists():
        console.print(f"[red]Error:[/red] Path does not exist: {repo_path}")
        raise typer.Exit(1)

    config = ZEAConfig(output_dir=output_dir, verbose=verbose)

    # --- Stage 1: Repository Discovery ---
    console.print(f"\n[bold blue]system-design[/bold blue] Analyzing [cyan]{repo_path.resolve().name}[/cyan]\n")

    with console.status("[bold green]Stage 1/3:[/bold green] Repository Discovery..."):
        inventory = scan_repository(repo_path, config)
        inv_path = config.output_path("repository_inventory.json")
        save_inventory(inventory, inv_path)

    _print_inventory_summary(inventory)

    # --- Stage 2: Build AKG skeleton ---
    with console.status("[bold green]Stage 2/3:[/bold green] Building Knowledge Graph..."):
        builder = AKGBuilder(inventory)
        akg = builder.build()

    # --- Stage 3: Architecture Inference ---
    if not skip_inference:
        with console.status("[bold green]Stage 3/3:[/bold green] Architecture Inference..."):
            engine = InferenceEngine(akg, repo_path)
            akg = engine.run()

    graph_path = config.output_path("architecture_graph.json")
    save_graph(akg, graph_path)

    # --- Summary ---
    console.print(f"\n[bold green]✓[/bold green] Analysis complete\n")
    console.print(f"  [dim]repository_inventory.json[/dim] → {inv_path}")
    console.print(f"  [dim]architecture_graph.json[/dim]  → {graph_path}")
    console.print(f"\n  Nodes: [bold]{akg.node_count}[/bold]  Edges: [bold]{akg.edge_count}[/bold]\n")


def _print_inventory_summary(inventory: object) -> None:
    from system_design.discovery.models import RepositoryInventory

    if not isinstance(inventory, RepositoryInventory):
        return

    table = Table(title="Repository Inventory", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim")
    table.add_column("Value")

    table.add_row("Name", inventory.repository_name)
    table.add_row("Primary Language", inventory.primary_language)
    table.add_row("Total Files", str(inventory.total_files))
    table.add_row(
        "Languages",
        ", ".join(f"{ls.language}({ls.file_count})" for ls in inventory.languages[:5]),
    )
    table.add_row(
        "Frameworks",
        ", ".join(f.framework for f in inventory.frameworks) or "None detected",
    )
    table.add_row(
        "Package Managers",
        ", ".join(p.manager for p in inventory.package_managers) or "None detected",
    )
    table.add_row("Has Tests", "✓" if inventory.has_tests else "✗")
    table.add_row("Has CI", "✓" if inventory.has_ci else "✗")

    console.print(table)
    console.print()
