"""Tests for the hotspot chart exporter."""
from __future__ import annotations

from pathlib import Path

from sauron.models import AnalysisResult, Hotspot
from sauron.reporters.chart_reporter import export_hotspot_chart


def _result() -> AnalysisResult:
    return AnalysisResult(
        repo_path="demo/repo",
        hotspots=[
            Hotspot(path="a.py", commit_count=10, churn=100, complexity=5.0, score=9.9),
            Hotspot(path="b.py", commit_count=5, churn=40, complexity=2.0, score=4.1),
        ],
    )


class TestExportHotspotChart:
    def test_creates_png_file(self, tmp_path: Path):
        out = export_hotspot_chart(_result(), tmp_path)
        assert out.exists()
        assert out.suffix == ".png"
        assert out.stat().st_size > 0

    def test_creates_output_dir(self, tmp_path: Path):
        target = tmp_path / "nested" / "reports"
        out = export_hotspot_chart(_result(), target)
        assert out.parent == target

    def test_handles_empty_hotspots(self, tmp_path: Path):
        out = export_hotspot_chart(AnalysisResult(repo_path="empty"), tmp_path)
        assert out.exists()
