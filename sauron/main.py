"""Sauron CLI — software repository mining tool."""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from sauron.analyzers.code_analyzer import analyze_code_metrics
from sauron.analyzers.git_analyzer import analyze_git_history
from sauron.analyzers.github_analyzer import analyze_github
from sauron.analyzers.hotspot_detector import detect_hotspots
from sauron.models import AnalysisResult
from sauron.reporters.file_reporter import export_csv, export_json
from sauron.reporters.terminal_reporter import print_analysis

app = typer.Typer(
    name="sauron",
    help="🔍 Software repository mining — identify maintenance problems.",
    add_completion=False,
    rich_markup_mode="rich",
)

_err = Console(stderr=True)


class OutputFormat(str, Enum):
    terminal = "terminal"
    csv = "csv"
    json = "json"


# ── Commands ──────────────────────────────────────────────────────────────────

@app.command()
def analyze(
    repo: Annotated[
        str,
        typer.Argument(help="Repository URL (GitHub) or local path."),
    ],
    github_token: Annotated[
        Optional[str],
        typer.Option(
            "--github-token",
            "-t",
            envvar="GITHUB_TOKEN",
            help="GitHub personal access token (or set GITHUB_TOKEN env var).",
            show_default=False,
        ),
    ] = None,
    output_format: Annotated[
        OutputFormat,
        typer.Option("--output", "-o", help="Output format."),
    ] = OutputFormat.terminal,
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-d", help="Directory for exported files."),
    ] = Path("."),
    since: Annotated[
        Optional[str],
        typer.Option("--since", help="Only analyse commits on/after YYYY-MM-DD."),
    ] = None,
    top_n: Annotated[
        int,
        typer.Option("--top", "-n", help="Show top N results per category."),
    ] = 10,
    skip_github: Annotated[
        bool,
        typer.Option("--no-github", help="Skip GitHub issue/PR analysis."),
    ] = False,
    skip_code: Annotated[
        bool,
        typer.Option("--no-code", help="Skip cyclomatic complexity metrics."),
    ] = False,
    skip_coupling: Annotated[
        bool,
        typer.Option("--no-coupling", help="Skip logical-coupling analysis."),
    ] = False,
    complexity_threshold: Annotated[
        int,
        typer.Option(
            "--complexity-threshold",
            help="Total cyclomatic complexity threshold for god-class detection.",
        ),
    ] = 50,
    method_threshold: Annotated[
        int,
        typer.Option(
            "--method-threshold",
            help="Function/method count threshold for god-class detection.",
        ),
    ] = 20,
) -> None:
    """
    [bold]Analyse a Git repository[/bold] for software maintenance problems.

    Produces hotspot rankings, logical-coupling maps, author statistics
    and (for GitHub repos) issue/PR health metrics.

    [bold]Examples[/bold]

      sauron analyze https://github.com/pallets/flask

      sauron analyze /path/to/local/repo --output csv --output-dir ./reports

      sauron analyze https://github.com/django/django --since 2024-01-01 --top 20

      sauron analyze https://github.com/owner/private --github-token ghp_…
    """
    # ── Validate --since ──────────────────────────────────────────────────
    since_dt: Optional[datetime] = None
    if since:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            _err.print(f"[red]Invalid --since value {since!r}.  Use YYYY-MM-DD.[/red]")
            raise typer.Exit(1)

    cloned_dir: Optional[str] = None
    local_path = repo
    is_remote = repo.startswith(("http://", "https://", "git@"))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=_err,
        transient=True,
    ) as progress:

        # ── Clone if remote ───────────────────────────────────────────────
        if is_remote:
            task = progress.add_task("Cloning repository…", total=None)
            try:
                from git import Repo as _GitRepo

                cloned_dir = tempfile.mkdtemp(prefix="sauron_")
                _GitRepo.clone_from(repo, cloned_dir)
                local_path = cloned_dir
            except Exception as exc:
                _err.print(f"[red]Failed to clone repository: {exc}[/red]")
                if cloned_dir:
                    shutil.rmtree(cloned_dir, ignore_errors=True)
                raise typer.Exit(1)
            progress.remove_task(task)

        # ── Git history ───────────────────────────────────────────────────
        task = progress.add_task("Analysing Git history…", total=None)
        try:
            file_metrics, logical_coupling, author_metrics = analyze_git_history(
                local_path, since=since_dt
            )
        except Exception as exc:
            _err.print(f"[red]Git analysis failed: {exc}[/red]")
            if cloned_dir:
                shutil.rmtree(cloned_dir, ignore_errors=True)
            raise typer.Exit(1)
        progress.remove_task(task)

        # ── Code metrics ──────────────────────────────────────────────────
        god_classes: list[str] = []
        if not skip_code:
            task = progress.add_task("Computing code complexity…", total=None)
            try:
                god_classes = analyze_code_metrics(
                    local_path,
                    file_metrics,
                    god_class_complexity=complexity_threshold,
                    god_class_methods=method_threshold,
                )
            except Exception as exc:
                _err.print(f"[yellow]Code metrics skipped: {exc}[/yellow]")
            progress.remove_task(task)

        # ── Hotspots ──────────────────────────────────────────────────────
        task = progress.add_task("Detecting hotspots…", total=None)
        hotspots = detect_hotspots(file_metrics, top_n=top_n)
        progress.remove_task(task)

        # ── GitHub ────────────────────────────────────────────────────────
        issue_metrics = None
        pr_metrics = None
        if not skip_github and is_remote:
            task = progress.add_task("Fetching GitHub data…", total=None)
            try:
                issue_metrics, pr_metrics = analyze_github(
                    repo, github_token=github_token
                )
            except Exception as exc:
                _err.print(f"[yellow]GitHub analysis skipped: {exc}[/yellow]")
            progress.remove_task(task)

    result = AnalysisResult(
        repo_path=repo,
        file_metrics=list(file_metrics.values()),
        hotspots=hotspots,
        logical_coupling=logical_coupling if not skip_coupling else [],
        author_metrics=author_metrics,
        issue_metrics=issue_metrics,
        pr_metrics=pr_metrics,
        god_classes=god_classes,
    )

    # ── Output ────────────────────────────────────────────────────────────
    if output_format == OutputFormat.terminal:
        print_analysis(result, top_n=top_n)
    elif output_format == OutputFormat.csv:
        export_csv(result, output_dir)
        _err.print(f"[green]CSV files written to {output_dir.resolve()}[/green]")
    elif output_format == OutputFormat.json:
        out = export_json(result, output_dir)
        _err.print(f"[green]JSON report written to {out}[/green]")

    # ── Cleanup ───────────────────────────────────────────────────────────
    if cloned_dir:
        shutil.rmtree(cloned_dir, ignore_errors=True)


@app.command()
def version() -> None:
    """Print the installed Sauron version."""
    from sauron import __version__

    typer.echo(f"sauron {__version__}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
