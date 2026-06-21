"""Unit tests for Sauron analyzers."""
from __future__ import annotations

import math

import pytest

from sauron.analyzers.hotspot_detector import detect_hotspots
from sauron.analyzers.github_analyzer import _extract_repo_name
from sauron.models import FileMetrics


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fm(path: str, commits: int, churn: int, complexity: float = 0.0) -> FileMetrics:
    fm = FileMetrics(path=path, commit_count=commits, churn=churn)
    fm.cyclomatic_complexity = complexity
    return fm


# ── HotspotDetector ───────────────────────────────────────────────────────────

class TestDetectHotspots:
    def test_empty_returns_empty(self):
        assert detect_hotspots({}) == []

    def test_orders_by_score_descending(self):
        metrics = {
            "low.py": _fm("low.py", commits=2, churn=10, complexity=1.0),
            "high.py": _fm("high.py", commits=100, churn=5000, complexity=20.0),
        }
        result = detect_hotspots(metrics, top_n=10)
        assert result[0].path == "high.py"

    def test_top_n_respected(self):
        metrics = {f"f{i}.py": _fm(f"f{i}.py", commits=i + 1, churn=i) for i in range(20)}
        assert len(detect_hotspots(metrics, top_n=5)) <= 5

    def test_score_formula(self):
        fm = _fm("a.py", commits=10, churn=0, complexity=5.0)
        result = detect_hotspots({"a.py": fm}, top_n=1)
        expected = round(math.log1p(10) * (1.0 + 5.0), 4)
        assert result[0].score == expected

    def test_zero_commits_excluded(self):
        metrics = {
            "active.py": _fm("active.py", commits=5, churn=50),
            "dead.py": _fm("dead.py", commits=0, churn=0),
        }
        paths = [h.path for h in detect_hotspots(metrics)]
        assert "active.py" in paths
        assert "dead.py" not in paths

    def test_returns_hotspot_fields(self):
        fm = _fm("x.py", commits=3, churn=30, complexity=2.0)
        h = detect_hotspots({"x.py": fm}, top_n=1)[0]
        assert h.path == "x.py"
        assert h.commit_count == 3
        assert h.churn == 30
        assert h.complexity == 2.0


# ── GitHub URL extractor ──────────────────────────────────────────────────────

class TestExtractRepoName:
    def test_https_url(self):
        assert _extract_repo_name("https://github.com/owner/repo") == "owner/repo"

    def test_https_url_with_git_suffix(self):
        assert _extract_repo_name("https://github.com/owner/repo.git") == "owner/repo"

    def test_https_url_trailing_slash(self):
        assert _extract_repo_name("https://github.com/owner/repo/") == "owner/repo"

    def test_ssh_url(self):
        assert _extract_repo_name("git@github.com:owner/repo.git") == "owner/repo"

    def test_non_github_returns_none(self):
        assert _extract_repo_name("https://gitlab.com/owner/repo") is None

    def test_local_path_returns_none(self):
        assert _extract_repo_name("/home/user/myrepo") is None
