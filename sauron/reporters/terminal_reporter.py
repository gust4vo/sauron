"""Rich-based terminal reporter."""
from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sauron.models import AnalysisResult

console = Console()


def print_analysis(result: AnalysisResult, top_n: int = 10) -> None:
    """Print a full analysis report to the terminal using Rich tables."""
    console.print(
        Panel.fit(
            f"[bold cyan]Sauron — Repository Analysis[/bold cyan]\n[dim]{result.repo_path}[/dim]",
            border_style="cyan",
        )
    )

    if result.hotspots:
        _print_hotspots(result, top_n)

    if result.logical_coupling:
        _print_logical_coupling(result, top_n)

    if result.author_metrics:
        _print_authors(result, top_n)

    if result.god_classes:
        _print_god_classes(result)

    if result.issue_metrics:
        _print_issue_metrics(result)

    if result.pr_metrics:
        _print_pr_metrics(result)


# ── Section printers ──────────────────────────────────────────────────────────

def _print_hotspots(result: AnalysisResult, top_n: int) -> None:
    n = min(top_n, len(result.hotspots))
    table = Table(title=f"🔥 Top {n} Hotspots", box=box.ROUNDED, highlight=True)
    table.add_column("File", style="cyan", no_wrap=False)
    table.add_column("Commits", justify="right", style="yellow")
    table.add_column("Churn", justify="right", style="magenta")
    table.add_column("Avg Complexity", justify="right", style="red")
    table.add_column("Score", justify="right", style="bold red")

    for h in result.hotspots[:top_n]:
        table.add_row(
            h.path,
            str(h.commit_count),
            str(h.churn),
            f"{h.complexity:.1f}" if h.complexity else "–",
            f"{h.score:.2f}",
        )
    console.print(table)


def _print_logical_coupling(result: AnalysisResult, top_n: int) -> None:
    n = min(top_n, len(result.logical_coupling))
    table = Table(title=f"🔗 Top {n} Logical Couplings", box=box.ROUNDED)
    table.add_column("File A", style="cyan")
    table.add_column("File B", style="cyan")
    table.add_column("Co-changes", justify="right", style="yellow")
    table.add_column("Coupling", justify="right", style="red")

    for lc in result.logical_coupling[:top_n]:
        table.add_row(
            lc.file_a,
            lc.file_b,
            str(lc.co_changes),
            f"{lc.coupling_degree:.1%}",
        )
    console.print(table)


def _print_authors(result: AnalysisResult, top_n: int) -> None:
    n = min(top_n, len(result.author_metrics))
    table = Table(title=f"👤 Top {n} Contributors", box=box.ROUNDED)
    table.add_column("Author", style="green")
    table.add_column("Commits", justify="right", style="yellow")
    table.add_column("Files Touched", justify="right")
    table.add_column("Lines +", justify="right", style="green")
    table.add_column("Lines −", justify="right", style="red")

    for a in result.author_metrics[:top_n]:
        table.add_row(
            a.name,
            str(a.commit_count),
            str(a.files_touched),
            str(a.lines_added),
            str(a.lines_removed),
        )
    console.print(table)


def _print_god_classes(result: AnalysisResult) -> None:
    table = Table(
        title=f"🧟 God Classes / Complex Files ({len(result.god_classes)})",
        box=box.ROUNDED,
    )
    table.add_column("File", style="red")
    for path in result.god_classes:
        table.add_row(path)
    console.print(table)


def _print_issue_metrics(result: AnalysisResult) -> None:
    im = result.issue_metrics
    table = Table(title="📋 GitHub Issue Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="yellow")

    table.add_row("Open issues", str(im.total_open))
    table.add_row("Closed issues", str(im.total_closed))
    table.add_row("Avg resolution time (days)", str(im.avg_resolution_days))
    table.add_row("Long-running issues (>90 d)", str(im.long_running_count))
    table.add_row("Reopened issues", str(im.reopened_count))
    console.print(table)


def _print_pr_metrics(result: AnalysisResult) -> None:
    pm = result.pr_metrics
    table = Table(title="🔀 GitHub Pull Request Metrics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="yellow")

    table.add_row("Open PRs", str(pm.total_open))
    table.add_row("Merged PRs", str(pm.total_merged))
    table.add_row("Rejected PRs", str(pm.total_closed_unmerged))
    table.add_row("Rejection rate", f"{pm.rejection_rate:.1%}")
    table.add_row("Avg review time (days)", str(pm.avg_review_time_days))
    table.add_row("Long-running PRs (>90 d)", str(pm.long_running_count))
    console.print(table)
