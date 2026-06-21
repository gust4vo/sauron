"""CSV and JSON file exporters."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from sauron.models import AnalysisResult


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def export_csv(result: AnalysisResult, output_dir: Path) -> None:
    """Write per-category CSV files into *output_dir*."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = output_dir / f"sauron_{_timestamp()}"

    # Hotspots
    if result.hotspots:
        with open(f"{prefix}_hotspots.csv", "w", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=["path", "commit_count", "churn", "complexity", "score"]
            )
            w.writeheader()
            for h in result.hotspots:
                w.writerow(
                    {
                        "path": h.path,
                        "commit_count": h.commit_count,
                        "churn": h.churn,
                        "complexity": h.complexity,
                        "score": h.score,
                    }
                )

    # Logical coupling
    if result.logical_coupling:
        with open(f"{prefix}_coupling.csv", "w", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=["file_a", "file_b", "co_changes", "coupling_degree"]
            )
            w.writeheader()
            for lc in result.logical_coupling:
                w.writerow(
                    {
                        "file_a": lc.file_a,
                        "file_b": lc.file_b,
                        "co_changes": lc.co_changes,
                        "coupling_degree": lc.coupling_degree,
                    }
                )

    # Authors
    if result.author_metrics:
        with open(f"{prefix}_authors.csv", "w", newline="") as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    "name",
                    "email",
                    "commit_count",
                    "files_touched",
                    "lines_added",
                    "lines_removed",
                ],
            )
            w.writeheader()
            for a in result.author_metrics:
                w.writerow(
                    {
                        "name": a.name,
                        "email": a.email,
                        "commit_count": a.commit_count,
                        "files_touched": a.files_touched,
                        "lines_added": a.lines_added,
                        "lines_removed": a.lines_removed,
                    }
                )

    # God classes
    if result.god_classes:
        with open(f"{prefix}_god_classes.csv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["path"])
            w.writeheader()
            for path in result.god_classes:
                w.writerow({"path": path})


def export_json(result: AnalysisResult, output_dir: Path) -> Path:
    """Write a single JSON report into *output_dir* and return its path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"sauron_{_timestamp()}_report.json"

    data: dict = {
        "repo": result.repo_path,
        "hotspots": [
            {
                "path": h.path,
                "commit_count": h.commit_count,
                "churn": h.churn,
                "complexity": h.complexity,
                "score": h.score,
            }
            for h in result.hotspots
        ],
        "logical_coupling": [
            {
                "file_a": lc.file_a,
                "file_b": lc.file_b,
                "co_changes": lc.co_changes,
                "coupling_degree": lc.coupling_degree,
            }
            for lc in result.logical_coupling
        ],
        "authors": [
            {
                "name": a.name,
                "email": a.email,
                "commit_count": a.commit_count,
                "files_touched": a.files_touched,
                "lines_added": a.lines_added,
                "lines_removed": a.lines_removed,
            }
            for a in result.author_metrics
        ],
        "god_classes": result.god_classes,
        "issue_metrics": (
            {
                "total_open": result.issue_metrics.total_open,
                "total_closed": result.issue_metrics.total_closed,
                "avg_resolution_days": result.issue_metrics.avg_resolution_days,
                "long_running_count": result.issue_metrics.long_running_count,
                "reopened_count": result.issue_metrics.reopened_count,
            }
            if result.issue_metrics
            else None
        ),
        "pr_metrics": (
            {
                "total_open": result.pr_metrics.total_open,
                "total_merged": result.pr_metrics.total_merged,
                "total_closed_unmerged": result.pr_metrics.total_closed_unmerged,
                "rejection_rate": result.pr_metrics.rejection_rate,
                "avg_review_time_days": result.pr_metrics.avg_review_time_days,
                "long_running_count": result.pr_metrics.long_running_count,
            }
            if result.pr_metrics
            else None
        ),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path
