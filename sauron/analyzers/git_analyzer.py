"""Git history analysis using PyDriller."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from itertools import combinations
from typing import Optional

from pydriller import Repository

from sauron.models import AuthorMetrics, FileMetrics, LogicalCoupling


def analyze_git_history(
    repo_path: str,
    since: Optional[datetime] = None,
    to: Optional[datetime] = None,
) -> tuple[dict[str, FileMetrics], list[LogicalCoupling], list[AuthorMetrics]]:
    """
    Walk the full Git history of *repo_path* and return per-file metrics,
    logical couplings and per-author contribution stats.

    Parameters
    ----------
    repo_path:
        Absolute path to a local Git repository.
    since:
        Only consider commits on or after this date.
    to:
        Only consider commits up to and including this date.

    Returns
    -------
    (file_metrics, logical_couplings, author_metrics)
    """
    file_data: dict[str, FileMetrics] = {}
    commit_files: list[list[str]] = []  # list of files changed per commit
    author_data: dict[str, AuthorMetrics] = {}
    author_files: dict[str, set[str]] = {}  # distinct paths touched per author

    kwargs: dict = {"path_to_repo": repo_path}
    if since:
        kwargs["since"] = since
    if to:
        kwargs["to"] = to

    for commit in Repository(**kwargs).traverse_commits():
        changed_paths: list[str] = []

        # ── Author tracking ────────────────────────────────────────────────
        author_key = commit.author.email or commit.author.name
        if author_key not in author_data:
            author_data[author_key] = AuthorMetrics(
                name=commit.author.name,
                email=commit.author.email or "",
            )
            author_files[author_key] = set()
        author_data[author_key].commit_count += 1

        # ── Per-file metrics ───────────────────────────────────────────────
        for mod in commit.modified_files:
            path = mod.new_path or mod.old_path
            if path is None:
                continue

            if path not in file_data:
                file_data[path] = FileMetrics(path=path)

            fm = file_data[path]
            added = mod.added_lines or 0
            removed = mod.deleted_lines or 0

            fm.commit_count += 1
            fm.lines_added += added
            fm.lines_removed += removed
            fm.churn += added + removed
            fm.authors.add(author_key)
            fm.last_modified = commit.committer_date.isoformat()

            author_data[author_key].lines_added += added
            author_data[author_key].lines_removed += removed
            author_files[author_key].add(path)

            changed_paths.append(path)

        if len(changed_paths) > 1:
            commit_files.append(changed_paths)

    # ── Distinct files touched per author ──────────────────────────────────
    for key, paths in author_files.items():
        author_data[key].files_touched = len(paths)

    # ── Logical coupling ───────────────────────────────────────────────────
    coupling_counter: Counter = Counter()
    for paths in commit_files:
        for a, b in combinations(sorted(set(paths)), 2):
            coupling_counter[(a, b)] += 1

    file_commit_count = {p: fm.commit_count for p, fm in file_data.items()}
    logical_couplings: list[LogicalCoupling] = []
    for (a, b), count in coupling_counter.most_common():
        if count < 2:
            break
        min_commits = min(
            file_commit_count.get(a, 1),
            file_commit_count.get(b, 1),
        )
        degree = count / min_commits if min_commits > 0 else 0.0
        logical_couplings.append(
            LogicalCoupling(
                file_a=a,
                file_b=b,
                co_changes=count,
                coupling_degree=round(degree, 4),
            )
        )

    return (
        file_data,
        sorted(logical_couplings, key=lambda lc: lc.coupling_degree, reverse=True),
        sorted(author_data.values(), key=lambda a: a.commit_count, reverse=True),
    )
