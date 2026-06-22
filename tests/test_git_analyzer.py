"""Integration tests for the Git history analyzer."""
from __future__ import annotations

from pathlib import Path

import pytest
from git import Actor, Repo

from sauron.analyzers.git_analyzer import analyze_git_history


def _commit(repo: Repo, path: Path, content: str, author: Actor, message: str) -> None:
    path.write_text(content)
    repo.index.add([str(path)])
    repo.index.commit(message, author=author, committer=author)


@pytest.fixture
def repo_dir(tmp_path: Path) -> Path:
    """A small repo where one author touches the same file twice plus another file."""
    repo = Repo.init(tmp_path)
    alice = Actor("Alice", "alice@example.com")

    a = tmp_path / "a.py"
    b = tmp_path / "b.py"
    _commit(repo, a, "x = 1\n", alice, "add a")
    _commit(repo, a, "x = 1\ny = 2\n", alice, "edit a")
    _commit(repo, b, "z = 3\n", alice, "add b")
    return tmp_path


class TestFilesTouched:
    def test_counts_distinct_files_not_modifications(self, repo_dir: Path):
        _, _, authors = analyze_git_history(str(repo_dir))
        alice = next(a for a in authors if a.email == "alice@example.com")
        # a.py was modified in two commits, b.py in one -> 2 distinct files.
        assert alice.files_touched == 2
        assert alice.commit_count == 3
