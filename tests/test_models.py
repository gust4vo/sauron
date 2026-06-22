"""Unit tests for Sauron data models."""
from __future__ import annotations

from sauron.models import (
    AnalysisResult,
    AuthorMetrics,
    FileMetrics,
    Hotspot,
    IssueMetrics,
    LogicalCoupling,
    PRMetrics,
)


class TestFileMetrics:
    def test_defaults(self):
        fm = FileMetrics(path="foo.py")
        assert fm.commit_count == 0
        assert fm.churn == 0
        assert fm.lines_added == 0
        assert fm.lines_removed == 0
        assert fm.authors == set()
        assert fm.cyclomatic_complexity == 0.0
        assert fm.last_modified is None

    def test_authors_is_independent_per_instance(self):
        a = FileMetrics(path="a.py")
        b = FileMetrics(path="b.py")
        a.authors.add("alice")
        assert "alice" not in b.authors

    def test_churn_assignment(self):
        fm = FileMetrics(path="x.py", churn=200, lines_added=150, lines_removed=50)
        assert fm.churn == 200
        assert fm.lines_added == 150
        assert fm.lines_removed == 50


class TestHotspot:
    def test_fields(self):
        h = Hotspot(path="hot.py", commit_count=10, churn=500, complexity=8.0, score=23.03)
        assert h.path == "hot.py"
        assert h.score == 23.03


class TestLogicalCoupling:
    def test_fields(self):
        lc = LogicalCoupling(file_a="a.py", file_b="b.py", co_changes=5, coupling_degree=0.5)
        assert lc.file_a == "a.py"
        assert lc.coupling_degree == 0.5


class TestAuthorMetrics:
    def test_defaults(self):
        am = AuthorMetrics(name="Alice", email="alice@example.com")
        assert am.commit_count == 0
        assert am.files_touched == 0
        assert am.lines_added == 0
        assert am.lines_removed == 0


class TestIssueMetrics:
    def test_fields(self):
        im = IssueMetrics(
            total_open=10,
            total_closed=40,
            avg_resolution_days=3.5,
            long_running_count=2,
            reopened_count=1,
        )
        assert im.total_open + im.total_closed == 50
        assert im.avg_resolution_days == 3.5


class TestPRMetrics:
    def test_rejection_rate_range(self):
        pr = PRMetrics(
            total_open=5,
            total_merged=80,
            total_closed_unmerged=20,
            rejection_rate=0.2,
            avg_review_time_days=1.5,
            long_running_count=3,
        )
        assert 0.0 <= pr.rejection_rate <= 1.0


class TestAnalysisResult:
    def test_defaults(self):
        ar = AnalysisResult(repo_path="/tmp/repo")
        assert ar.file_metrics == []
        assert ar.hotspots == []
        assert ar.logical_coupling == []
        assert ar.author_metrics == []
        assert ar.issue_metrics is None
        assert ar.pr_metrics is None
        assert ar.god_classes == []

    def test_lists_are_independent(self):
        ar1 = AnalysisResult(repo_path="/tmp/a")
        ar2 = AnalysisResult(repo_path="/tmp/b")
        ar1.god_classes.append("god.py")
        assert ar2.god_classes == []
