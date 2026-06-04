"""ZEA CLI entrypoint."""
from __future__ import annotations

import typer
from rich.console import Console

from zea.cli.commands.analyze import analyze_command

app = typer.Typer(
    name="zea",
    help="ZEA — Zealous Engine for Architectures: Architecture Intelligence Engine",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


@app.command("analyze")
def analyze(
    repo_path: str = typer.Argument(..., help="Path to repository"),
    output_dir: str = typer.Option(".zea", "--output", "-o"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    skip_inference: bool = typer.Option(False, "--no-inference"),
) -> None:
    """Analyze a repository: Discovery → Graph → Inference."""
    from pathlib import Path
    analyze_command(
        repo_path=Path(repo_path),
        output_dir=Path(output_dir),
        verbose=verbose,
        skip_inference=skip_inference,
    )


@app.command("visualize")
def visualize(
    graph_path: str = typer.Argument(..., help="Path to architecture_graph.json"),
    output: str = typer.Option("architecture.html", "--output", "-o", help="Output HTML file path"),
) -> None:
    """Generate a standalone 3D interactive architecture visualisation."""
    from pathlib import Path
    from zea.visualization.threejs_generator import generate_html_from_file

    src = Path(graph_path)
    if not src.exists():
        console.print(f"[bold red]Error:[/bold red] File not found: {graph_path}")
        raise typer.Exit(code=1)

    out = generate_html_from_file(src, Path(output))
    console.print(f"[bold green]✓[/bold green] 3D visualisation written to [bold]{out}[/bold]")


@app.command("ai-analyze")
def ai_analyze(
    repo_path: str = typer.Argument(..., help="Path to repository"),
    output_dir: str = typer.Option(".zea", "--output", "-o"),
    model: str = typer.Option("claude-opus-4-6", "--model", "-m", help="Claude model to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Full AI pipeline: Scan → Claude Analysis → 3D System Design."""
    from pathlib import Path
    from zea.cli.commands.ai_analyze import ai_analyze_command
    ai_analyze_command(
        repo_path=Path(repo_path),
        output_dir=Path(output_dir),
        model=model,
        verbose=verbose,
    )


@app.command("version")
def version() -> None:
    """Show ZEA version."""
    console.print("[bold blue]ZEA[/bold blue] v0.1.0 — Architecture Intelligence Engine")


if __name__ == "__main__":
    app()
