"""Static code-quality analysis using Lizard."""
from __future__ import annotations

import os

import lizard

from sauron.models import FileMetrics

# Default thresholds for "god class" detection
_COMPLEXITY_THRESHOLD = 50  # sum of cyclomatic complexity across all functions
_METHOD_THRESHOLD = 20       # number of functions/methods in the file


def analyze_code_metrics(
    repo_path: str,
    file_metrics: dict[str, FileMetrics],
    god_class_complexity: int = _COMPLEXITY_THRESHOLD,
    god_class_methods: int = _METHOD_THRESHOLD,
) -> list[str]:
    """
    Compute cyclomatic complexity and function-size metrics for every file
    tracked in *file_metrics*, updating the ``FileMetrics`` objects in-place.

    Returns a list of file paths that exceed the god-class thresholds.
    """
    god_classes: list[str] = []

    for file_path, fm in file_metrics.items():
        full_path = os.path.join(repo_path, file_path)
        if not os.path.isfile(full_path):
            continue

        try:
            file_info = lizard.analyze_file(full_path)
        except Exception:
            continue

        if file_info is None:
            continue

        functions = file_info.function_list
        if not functions:
            continue

        total_complexity = sum(f.cyclomatic_complexity for f in functions)
        avg_complexity = total_complexity / len(functions)
        lengths = [f.length for f in functions]
        avg_length = sum(lengths) / len(lengths)
        max_length = max(lengths)

        fm.cyclomatic_complexity = round(avg_complexity, 2)
        fm.avg_function_length = round(avg_length, 2)
        fm.max_function_length = max_length
        fm.function_count = len(functions)

        if total_complexity >= god_class_complexity or len(functions) >= god_class_methods:
            god_classes.append(file_path)

    return god_classes
