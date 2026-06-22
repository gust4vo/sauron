"""Matplotlib-based chart exporter for hotspots."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend — no display required
import matplotlib.pyplot as plt  # noqa: E402

from sauron.models import AnalysisResult  # noqa: E402


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def export_hotspot_chart(
    result: AnalysisResult,
    output_dir: Path,
    top_n: int = 10,
) -> Path:
    """
    Render the top *top_n* hotspots as a horizontal bar chart (by score)
    and save it as a PNG inside *output_dir*.  Returns the file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"sauron_{_timestamp()}_hotspots.png"

    hotspots = result.hotspots[:top_n]
    # Highest score on top of a horizontal bar chart.
    labels = [h.path for h in reversed(hotspots)]
    scores = [h.score for h in reversed(hotspots)]

    height = max(2.0, 0.5 * len(labels) + 1.0)
    fig, ax = plt.subplots(figsize=(10, height))
    ax.barh(labels, scores, color="#c0392b")
    ax.set_xlabel("Hotspot score")
    ax.set_title(f"Sauron — Top {len(labels)} Hotspots\n{result.repo_path}")
    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)

    return output_path
