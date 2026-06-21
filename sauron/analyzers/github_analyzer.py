"""GitHub issue and pull-request analysis via PyGithub."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from github import Auth, Github, GithubException

from sauron.models import IssueMetrics, PRMetrics

_GITHUB_URL_RE = re.compile(
    r"github\.com[/:](?P<owner>[^/]+)/(?P<repo>[^/\s.]+?)(?:\.git)?/?$"
)


def _extract_repo_name(repo_url: str) -> Optional[str]:
    """Return 'owner/repo' from a GitHub URL, or *None* if not a GitHub URL."""
    m = _GITHUB_URL_RE.search(repo_url)
    if m:
        return f"{m.group('owner')}/{m.group('repo')}"
    return None


def analyze_github(
    repo_url: str,
    github_token: Optional[str] = None,
    long_days: int = 90,
    max_items: int = 100,
) -> tuple[Optional[IssueMetrics], Optional[PRMetrics]]:
    """
    Fetch issue and pull-request statistics from a GitHub repository.

    Parameters
    ----------
    repo_url:
        Full GitHub URL, e.g. ``https://github.com/owner/repo``.
    github_token:
        Personal access token.  Anonymous requests are used if *None*
        (lower rate limits apply).
    long_days:
        Number of days after which an open issue/PR is considered long-running.
    max_items:
        Maximum number of issues / PRs to fetch (avoids timeouts on large repos).

    Returns
    -------
    ``(IssueMetrics, PRMetrics)`` — either can be *None* on failure.
    """
    repo_name = _extract_repo_name(repo_url)
    if not repo_name:
        return None, None

    try:
        auth = Auth.Token(github_token) if github_token else None
        gh = Github(auth=auth)
        repo = gh.get_repo(repo_name)
    except GithubException:
        return None, None

    now = datetime.now(timezone.utc)

    # ── Issues ────────────────────────────────────────────────────────────
    issue_metrics: Optional[IssueMetrics] = None
    try:
        raw_issues = list(repo.get_issues(state="all")[:max_items])
        real_issues = [i for i in raw_issues if i.pull_request is None]
        open_issues = [i for i in real_issues if i.state == "open"]
        closed_issues = [i for i in real_issues if i.state == "closed"]

        resolution_times: list[float] = []
        for issue in closed_issues:
            if issue.closed_at and issue.created_at:
                delta = (issue.closed_at - issue.created_at).total_seconds() / 86400
                resolution_times.append(delta)

        long_running = sum(
            1
            for i in open_issues
            if (now - i.created_at.replace(tzinfo=timezone.utc)).days > long_days
        )

        issue_metrics = IssueMetrics(
            total_open=len(open_issues),
            total_closed=len(closed_issues),
            avg_resolution_days=(
                round(sum(resolution_times) / len(resolution_times), 1)
                if resolution_times
                else 0.0
            ),
            long_running_count=long_running,
            reopened_count=0,
        )
    except GithubException:
        pass

    # ── Pull Requests ─────────────────────────────────────────────────────
    pr_metrics: Optional[PRMetrics] = None
    try:
        prs = list(repo.get_pulls(state="all")[:max_items])
        open_prs = [p for p in prs if p.state == "open"]
        merged_prs = [p for p in prs if p.merged]
        rejected_prs = [p for p in prs if p.state == "closed" and not p.merged]

        review_times: list[float] = []
        for pr in merged_prs:
            if pr.merged_at and pr.created_at:
                delta = (pr.merged_at - pr.created_at).total_seconds() / 86400
                review_times.append(delta)

        total_closed = len(merged_prs) + len(rejected_prs)
        rejection_rate = len(rejected_prs) / total_closed if total_closed > 0 else 0.0

        long_running_prs = sum(
            1
            for p in open_prs
            if (now - p.created_at.replace(tzinfo=timezone.utc)).days > long_days
        )

        pr_metrics = PRMetrics(
            total_open=len(open_prs),
            total_merged=len(merged_prs),
            total_closed_unmerged=len(rejected_prs),
            rejection_rate=round(rejection_rate, 4),
            avg_review_time_days=(
                round(sum(review_times) / len(review_times), 1) if review_times else 0.0
            ),
            long_running_count=long_running_prs,
        )
    except GithubException:
        pass

    return issue_metrics, pr_metrics
