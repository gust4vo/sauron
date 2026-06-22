"""Unit tests for the GitHub analyzer helpers."""
from __future__ import annotations

from github import GithubException

from sauron.analyzers.github_analyzer import _count_reopened


class _FakeEvent:
    def __init__(self, event: str) -> None:
        self.event = event


class _FakeIssue:
    def __init__(self, events: list[str]) -> None:
        self._events = events

    def get_events(self):
        return [_FakeEvent(e) for e in self._events]


class _BrokenIssue:
    def get_events(self):
        raise GithubException(404, "not found", None)


class TestCountReopened:
    def test_empty(self):
        assert _count_reopened([]) == 0

    def test_counts_only_reopened_issues(self):
        issues = [
            _FakeIssue(["closed", "reopened", "closed"]),
            _FakeIssue(["closed"]),
            _FakeIssue(["labeled", "reopened"]),
        ]
        assert _count_reopened(issues) == 2

    def test_reopened_counted_once_per_issue(self):
        issues = [_FakeIssue(["reopened", "closed", "reopened"])]
        assert _count_reopened(issues) == 1

    def test_skips_issues_with_fetch_errors(self):
        issues = [_BrokenIssue(), _FakeIssue(["reopened"])]
        assert _count_reopened(issues) == 1
