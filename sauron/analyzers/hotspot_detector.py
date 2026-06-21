"""Hotspot detection: combine commit frequency with cyclomatic complexity."""
from __future__ import annotations

import math

from sauron.models import FileMetrics, Hotspot


def detect_hotspots(
    file_metrics: dict[str, FileMetrics],
    top_n: int = 10,
) -> list[Hotspot]:
    """
    Rank files by a composite *hotspot score*:

        score = log(1 + commit_count) × (1 + avg_cyclomatic_complexity)

    Files with zero commits are excluded.  Returns the top *top_n* results
    sorted by descending score.
    """
    hotspots: list[Hotspot] = []

    for path, fm in file_metrics.items():
        if fm.commit_count == 0:
            continue

        score = math.log1p(fm.commit_count) * (1.0 + fm.cyclomatic_complexity)
        hotspots.append(
            Hotspot(
                path=path,
                commit_count=fm.commit_count,
                churn=fm.churn,
                complexity=fm.cyclomatic_complexity,
                score=round(score, 4),
            )
        )

    return sorted(hotspots, key=lambda h: h.score, reverse=True)[:top_n]
