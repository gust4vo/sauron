"""Unit tests for the static code analyzer (analyze_code_metrics)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from sauron.analyzers.code_analyzer import analyze_code_metrics
from sauron.models import FileMetrics


def _write(tmp_path: Path, filename: str, source: str) -> Path:
    p = tmp_path / filename
    p.write_text(textwrap.dedent(source))
    return p


# ── analyze_code_metrics ──────────────────────────────────────────────────────

class TestAnalyzeCodeMetrics:
    def test_missing_file_is_skipped(self, tmp_path):
        fm = FileMetrics(path="nonexistent.py")
        god_classes = analyze_code_metrics(str(tmp_path), {"nonexistent.py": fm})
        assert god_classes == []
        # metrics should remain at defaults
        assert fm.function_count == 0
        assert fm.cyclomatic_complexity == 0.0

    def test_simple_function_metrics(self, tmp_path):
        _write(tmp_path, "simple.py", """\
            def add(a, b):
                return a + b

            def subtract(a, b):
                return a - b
        """)
        fm = FileMetrics(path="simple.py")
        god_classes = analyze_code_metrics(str(tmp_path), {"simple.py": fm})

        assert god_classes == []
        assert fm.function_count == 2
        assert fm.cyclomatic_complexity >= 1.0
        assert fm.avg_function_length > 0
        assert fm.max_function_length > 0

    def test_complex_file_detected_as_god_class(self, tmp_path):
        # Build a file with many functions to exceed the method threshold (20)
        funcs = "\n".join(
            f"def func_{i}(x):\n    if x > {i}:\n        return x\n    return 0\n"
            for i in range(25)
        )
        (tmp_path / "big.py").write_text(funcs)

        fm = FileMetrics(path="big.py")
        god_classes = analyze_code_metrics(
            str(tmp_path), {"big.py": fm}, god_class_methods=20
        )
        assert "big.py" in god_classes

    def test_below_threshold_not_flagged(self, tmp_path):
        _write(tmp_path, "small.py", """\
            def one():
                return 1

            def two():
                return 2
        """)
        fm = FileMetrics(path="small.py")
        god_classes = analyze_code_metrics(
            str(tmp_path),
            {"small.py": fm},
            god_class_complexity=1000,
            god_class_methods=1000,
        )
        assert "small.py" not in god_classes

    def test_empty_file_not_flagged(self, tmp_path):
        (tmp_path / "empty.py").write_text("")
        fm = FileMetrics(path="empty.py")
        god_classes = analyze_code_metrics(str(tmp_path), {"empty.py": fm})
        assert god_classes == []
        assert fm.function_count == 0

    def test_metrics_updated_in_place(self, tmp_path):
        _write(tmp_path, "inplace.py", """\
            def greet(name):
                return f"Hello, {name}"
        """)
        fm = FileMetrics(path="inplace.py")
        file_metrics = {"inplace.py": fm}
        analyze_code_metrics(str(tmp_path), file_metrics)

        # same object should be mutated
        assert file_metrics["inplace.py"].function_count == 1

    def test_multiple_files_processed(self, tmp_path):
        for name in ("a.py", "b.py", "c.py"):
            _write(tmp_path, name, "def f():\n    return 1\n")

        metrics = {n: FileMetrics(path=n) for n in ("a.py", "b.py", "c.py")}
        analyze_code_metrics(str(tmp_path), metrics)

        for fm in metrics.values():
            assert fm.function_count == 1
