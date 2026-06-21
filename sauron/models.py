"""Data models for Sauron analysis results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileMetrics:
    """Per-file metrics aggregated from Git history and static analysis."""

    path: str
    commit_count: int = 0
    churn: int = 0  # total lines added + removed
    lines_added: int = 0
    lines_removed: int = 0
    authors: set[str] = field(default_factory=set)
    cyclomatic_complexity: float = 0.0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    function_count: int = 0
    last_modified: Optional[str] = None


@dataclass
class Hotspot:
    """A file identified as a maintenance hotspot (high churn + high complexity)."""

    path: str
    commit_count: int
    churn: int
    complexity: float
    score: float  # composite score: log(1+commits) * (1+complexity)


@dataclass
class LogicalCoupling:
    """Two files that are frequently changed together in the same commit."""

    file_a: str
    file_b: str
    co_changes: int
    coupling_degree: float  # co_changes / min(commits_a, commits_b)


@dataclass
class AuthorMetrics:
    """Per-author contribution statistics."""

    name: str
    email: str
    commit_count: int = 0
    files_touched: int = 0
    lines_added: int = 0
    lines_removed: int = 0


@dataclass
class IssueMetrics:
    """GitHub issue statistics."""

    total_open: int
    total_closed: int
    avg_resolution_days: float
    long_running_count: int  # open > long_issue_days
    reopened_count: int


@dataclass
class PRMetrics:
    """GitHub pull-request statistics."""

    total_open: int
    total_merged: int
    total_closed_unmerged: int  # rejected PRs
    rejection_rate: float
    avg_review_time_days: float
    long_running_count: int  # open > long_issue_days


@dataclass
class AnalysisResult:
    """Container for all analysis results from a single repository run."""

    repo_path: str
    file_metrics: list[FileMetrics] = field(default_factory=list)
    hotspots: list[Hotspot] = field(default_factory=list)
    logical_coupling: list[LogicalCoupling] = field(default_factory=list)
    author_metrics: list[AuthorMetrics] = field(default_factory=list)
    issue_metrics: Optional[IssueMetrics] = None
    pr_metrics: Optional[PRMetrics] = None
    god_classes: list[str] = field(default_factory=list)
