from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import sys

if "--headless" in sys.argv:
    matplotlib.use("Agg")

from plot_utils import VERSION_LABELS, get_config_value, read_log, load_logs

def plot_astar_performance(logs):
    grouped = defaultdict(list)

    for log in logs:
        version = get_config_value(log, "version")

        if version is None:
            continue

        label = VERSION_LABELS.get(version, f"Unknown ({version})")

        for state in log["states"]:
            time_ms = state.get("planner_time_ms")

            if time_ms is not None:
                grouped[label].append(time_ms)

    if not grouped:
        return

    labels = [
        label for label in VERSION_LABELS.values()
        if label in grouped
    ]
    values = [grouped[label] for label in labels]

    figure, axis = plt.subplots(figsize=(8, 5))

    axis.boxplot(
        values,
        tick_labels=labels,
        showmeans=True,
    )

    axis.set_title("A* performance comparison")
    axis.set_xlabel("A* implementation")
    axis.set_ylabel("Execution time (ms)")
    axis.grid(axis="y", alpha=0.3)

    figure.tight_layout()


def plot_time_per_path_step(logs):
    grouped = defaultdict(list)

    for log in logs:
        version = get_config_value(log, "version")

        if version is None:
            continue

        label = VERSION_LABELS.get(version, f"Unknown ({version})")

        for state in log["states"]:
            path_length = state.get("path_length")
            execution_time = state.get("planner_time_ms")

            if (
                path_length is not None
                and execution_time is not None
                and path_length > 0
            ):
                score = execution_time / path_length
                grouped[label].append(score)

    if not grouped:
        return

    labels = [
        label for label in VERSION_LABELS.values()
        if label in grouped
    ]
    values = [grouped[label] for label in labels]

    figure, axis = plt.subplots(figsize=(8, 5))

    axis.boxplot(
        values,
        tick_labels=labels,
        showmeans=True,
    )

    axis.set_title("A* execution time per path step")
    axis.set_xlabel("A* implementation")
    axis.set_ylabel("Execution time / path length (ms per step)")
    axis.grid(axis="y", alpha=0.3)

    figure.tight_layout()


def plot_astar_statistics(logs):
    grouped = defaultdict(list)

    for log in logs:
        version = get_config_value(log, "version")

        if version is None:
            continue

        label = VERSION_LABELS.get(version, f"Unknown ({version})")

        for state in log["states"]:
            execution_time = state.get("planner_time_ms")

            if execution_time is not None:
                grouped[label].append(execution_time)

    labels = [
        label for label in VERSION_LABELS.values()
        if label in grouped
    ]

    if not labels:
        return

    rows = []

    for label in labels:
        values = np.asarray(grouped[label], dtype=float)

        rows.append([
            label,
            len(values),
            f"{np.mean(values):.4f}",
            f"{np.median(values):.4f}",
            f"{np.min(values):.4f}",
            f"{np.max(values):.4f}",
            f"{np.std(values):.4f}",
        ])

    figure, axis = plt.subplots(figsize=(11, 3.5))
    axis.axis("off")

    table = axis.table(
        cellText=rows,
        colLabels=[
            "Version",
            "N",
            "Mean (ms)",
            "Median (ms)",
            "Min (ms)",
            "Max (ms)",
            "Std dev (ms)",
        ],
        loc="center",
        cellLoc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    axis.set_title(
        "A* execution-time statistics",
        pad=20,
    )

    figure.tight_layout()


def plot_execution_time_with_stats(logs):
    grouped = defaultdict(list)

    for log in logs:
        version = get_config_value(log, "version")

        if version is None:
            continue

        label = VERSION_LABELS.get(version, f"Unknown ({version})")

        for state in log["states"]:
            execution_time = state.get("planner_time_ms")

            if execution_time is not None:
                grouped[label].append(execution_time)

    labels = [
        label for label in VERSION_LABELS.values()
        if label in grouped
    ]

    if not labels:
        return

    figure, (plot_axis, table_axis) = plt.subplots(
        2,
        1,
        figsize=(9, 9),
        gridspec_kw={"height_ratios": [3, 1]},
    )

    rng = np.random.default_rng(42)

    for position, label in enumerate(labels, start=1):
        values = np.asarray(grouped[label], dtype=float)

        x_values = position + rng.uniform(
            -0.08,
            0.08,
            len(values),
        )

        plot_axis.scatter(
            x_values,
            values,
            alpha=0.35,
            s=14,
        )

        plot_axis.scatter(
            position,
            np.mean(values),
            color="red",
            marker="x",
            s=60,
            label="Mean" if position == 1 else None,
        )

    plot_axis.set_title("A* execution time")
    plot_axis.set_xlabel("A* implementation")
    plot_axis.set_ylabel("Execution time (ms)")
    plot_axis.set_xticks(
        range(1, len(labels) + 1),
        labels,
    )
    plot_axis.grid(axis="y", alpha=0.3)
    plot_axis.legend()

    rows = []

    for label in labels:
        values = np.asarray(grouped[label], dtype=float)

        rows.append([
            label,
            len(values),
            f"{np.mean(values):.4f}",
            f"{np.median(values):.4f}",
            f"{np.min(values):.4f}",
            f"{np.max(values):.4f}",
            f"{np.std(values):.4f}",
        ])

    table_axis.axis("off")
    table_axis.table(
        cellText=rows,
        colLabels=[
            "Version",
            "N",
            "Mean (ms)",
            "Median (ms)",
            "Min (ms)",
            "Max (ms)",
            "Std dev (ms)",
        ],
        loc="center",
        cellLoc="center",
    )

    figure.tight_layout()
