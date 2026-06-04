"""
ZEA Benchmark Runner.

Usage:
  python -m tests.benchmark.runner --quick
  python -m tests.benchmark.runner --all
  python -m tests.benchmark.runner --repo https://github.com/tiangolo/fastapi
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from tests.benchmark.metrics import combined_score, score_graph, score_inventory
from tests.benchmark.targets import BENCHMARK_TARGETS, TARGETS_BY_URL, BenchmarkTarget

app = typer.Typer(help="ZEA Benchmark Runner")
console = Console()

CLONE_BASE = Path("/tmp/zea_benchmarks")


# ---------------------------------------------------------------------------
# Clone helpers
# ---------------------------------------------------------------------------

def clone_repo(target: BenchmarkTarget) -> Path | None:
    """Clone a repo to /tmp/zea_benchmarks/<repo_name>. Skip if already exists."""
    dest = CLONE_BASE / target.repo_name
    if dest.exists():
        console.print(f"  [dim]Already cloned:[/dim] {dest}")
        return dest

    CLONE_BASE.mkdir(parents=True, exist_ok=True)
    console.print(f"  Cloning [cyan]{target.repo_url}[/cyan] ...")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", target.repo_url, str(dest)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            console.print(f"  [red]Clone failed:[/red] {result.stderr.strip()}")
            return None
        return dest
    except subprocess.TimeoutExpired:
        console.print("  [red]Clone timed out[/red]")
        return None
    except Exception as exc:
        console.print(f"  [red]Clone error:[/red] {exc}")
        return None


# ---------------------------------------------------------------------------
# ZEA analysis
# ---------------------------------------------------------------------------

def run_zea(repo_path: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Run ZEA analysis on a repo path using the Python API directly.

    Returns (inventory_dict, graph_dict) or (None, None) on failure.
    """
    try:
        from zea.core.config import ZEAConfig
        from zea.discovery.scanner import scan_repository
        from zea.graph.builder import AKGBuilder
        from zea.graph.serializer import save_graph
        from zea.inference.engine import InferenceEngine

        config = ZEAConfig()
        inventory = scan_repository(repo_path, config)
        inventory_dict = json.loads(json.dumps(inventory.model_dump(), default=str))

        builder = AKGBuilder(inventory)
        akg = builder.build()

        engine = InferenceEngine(akg, repo_path)
        akg = engine.run()

        graph_dict = json.loads(akg.model_dump_json())
        return inventory_dict, graph_dict

    except Exception as exc:
        console.print(f"  [red]ZEA analysis error:[/red] {exc}")
        return None, None


# ---------------------------------------------------------------------------
# Single target run
# ---------------------------------------------------------------------------

def run_target(
    target: BenchmarkTarget,
    quick: bool = False,
) -> dict[str, Any]:
    """Run benchmark for one target. Returns a result dict."""
    console.rule(f"[bold]{target.repo_name}[/bold]")
    console.print(f"  [dim]{target.description}[/dim]")

    repo_path = CLONE_BASE / target.repo_name

    if quick:
        if not repo_path.exists():
            console.print(f"  [yellow]SKIPPED[/yellow] (not cloned; run --all to clone)")
            return _skipped_result(target, reason="not_cloned")
    else:
        cloned = clone_repo(target)
        if cloned is None:
            return _skipped_result(target, reason="clone_failed")
        repo_path = cloned

    console.print(f"  Running ZEA analysis on [cyan]{repo_path}[/cyan] ...")
    inventory_dict, graph_dict = run_zea(repo_path)

    if inventory_dict is None or graph_dict is None:
        return _skipped_result(target, reason="analysis_failed")

    inv_scores = score_inventory(inventory_dict, target)
    grph_scores = score_graph(graph_dict, target)
    overall = combined_score(inv_scores, grph_scores)

    console.print(
        f"  Language F1: [bold]{inv_scores['language_f1']}[/bold]  "
        f"Framework F1: [bold]{inv_scores['framework_f1']}[/bold]  "
        f"Node Types: [bold]{grph_scores['node_types_met']}[/bold]  "
        f"Overall: [bold green]{overall}[/bold green]"
    )

    return {
        "repo": target.repo_name,
        "repo_url": target.repo_url,
        "status": "ok",
        "inventory_scores": inv_scores,
        "graph_scores": grph_scores,
        "overall": overall,
    }


def _skipped_result(target: BenchmarkTarget, reason: str) -> dict[str, Any]:
    return {
        "repo": target.repo_name,
        "repo_url": target.repo_url,
        "status": "skipped",
        "reason": reason,
        "inventory_scores": {},
        "graph_scores": {},
        "overall": None,
    }


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------

def print_summary(results: list[dict[str, Any]]) -> None:
    console.rule("[bold blue]Benchmark Summary[/bold blue]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repo", style="bold")
    table.add_column("Status")
    table.add_column("Lang F1", justify="right")
    table.add_column("FW F1", justify="right")
    table.add_column("Node Types", justify="right")
    table.add_column("Overall", justify="right")

    for r in results:
        status = r["status"]
        if status != "ok":
            table.add_row(
                r["repo"],
                f"[yellow]{status}[/yellow]",
                "-", "-", "-", "-",
            )
            continue

        inv = r["inventory_scores"]
        grph = r["graph_scores"]
        overall = r["overall"]

        color = "green" if overall >= 0.85 else ("yellow" if overall >= 0.7 else "red")

        table.add_row(
            r["repo"],
            "[green]ok[/green]",
            str(inv.get("language_f1", "-")),
            str(inv.get("framework_f1", "-")),
            str(grph.get("node_types_met", "-")),
            f"[{color}]{overall}[/{color}]",
        )

    console.print(table)

    scored = [r for r in results if r["status"] == "ok" and r["overall"] is not None]
    if scored:
        avg = round(sum(r["overall"] for r in scored) / len(scored), 3)
        console.print(f"\n  Average overall score: [bold]{avg}[/bold]  ({len(scored)}/{len(results)} repos scored)")

    console.print()


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

@app.command()
def main(
    repo: str = typer.Option("", "--repo", help="Run against a specific repo URL"),
    all_repos: bool = typer.Option(False, "--all", help="Clone and run all benchmark targets"),
    quick: bool = typer.Option(False, "--quick", help="Only run against already-cloned repos"),
    output: Path = typer.Option(Path("benchmark_results.json"), "--output", "-o"),
) -> None:
    """Run ZEA benchmarks against real open-source repositories."""

    if repo:
        target = TARGETS_BY_URL.get(repo)
        if target is None:
            console.print(f"[red]Unknown repo URL:[/red] {repo}")
            console.print("Known targets:")
            for t in BENCHMARK_TARGETS:
                console.print(f"  {t.repo_url}")
            raise typer.Exit(1)
        targets = [target]
    elif all_repos or quick:
        targets = BENCHMARK_TARGETS
    else:
        console.print(
            "[yellow]No mode specified.[/yellow] Use --quick, --all, or --repo <url>.\n"
            "Run [bold]python -m tests.benchmark.runner --help[/bold] for usage."
        )
        raise typer.Exit(1)

    results: list[dict[str, Any]] = []
    for t in targets:
        result = run_target(t, quick=quick)
        results.append(result)

    print_summary(results)

    output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    console.print(f"Full results saved to [cyan]{output}[/cyan]")


if __name__ == "__main__":
    app()
