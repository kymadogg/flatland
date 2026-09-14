from collections import defaultdict
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import argparse

'''
Plot ideas:

time steps vs coverage
    - how many sim steps does it take to win based on percent coverage, 
    - are all 3 algos about the same when seed is controlled

average execution time vs 

coverage vs win rate:
    - 

enemy decay rate:
    - how long do enemies stick around 
'''

VERSION_LABELS = {
    0: "Python",
    1: "Rust (HashMap)",
    2: "Rust (heapq)",
}

def read_log(path):
    config = None
    states = []
    result = None

    with path.open(encoding="utf-8") as log_file:
        for line_number, line in enumerate(log_file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                print(f"Skipping {path}:{line_number}: {error}")
                continue

            record_type = record.get("type")

            if record_type == "config":
                config = record
            elif record_type == "state":
                states.append(record)
            elif record_type == "result":
                result = record

    return {
        "path": path,
        "config": config,
        "states": states,
        "result": result,
    }

def load_logs(data_dir):
    logs = []

    for path in sorted(data_dir.rglob("*.jsonl")):
        log = read_log(path)

        if log["config"] is not None:
            logs.append(log)

    return logs

def get_config_value(log, name, default=None):
    config = log["config"]

    if config is None:
        return default

    return config.get("config", {}).get(name, default)

def plot_average_teleports_vs_coverage(logs):
    grouped = defaultdict(list)

    for log in logs:
        coverage = get_config_value(log, "coverage")
        result = log["result"]

        if coverage is not None and result is not None:
            grouped[coverage].append(
                result.get("teleports", 0)
            )

    coverages = sorted(grouped)
    averages = [
        np.mean(grouped[coverage])
        for coverage in coverages
    ]

    figure, axis = plt.subplots(figsize=(8, 5))

    axis.plot(
        coverages,
        averages,
        marker="o",
        color="darkorange",
    )

    axis.set_title("Average teleports vs obstacle coverage")
    axis.set_xlabel("Obstacle coverage (%)")
    axis.set_ylabel("Average teleports")
    axis.grid(alpha=0.3)

    figure.tight_layout()

def plot_average_enemies_vs_timestep(logs):
    grouped = defaultdict(lambda: defaultdict(list))

    for log in logs:
        coverage = get_config_value(log, "coverage")

        if coverage is None:
            continue

        for state in log["states"]:
            if "step" not in state or "enemies" not in state:
                continue

            step = state["step"]
            enemy_count = len(state["enemies"])
            grouped[coverage][step].append(enemy_count)

    if not grouped:
        return

    coverages = sorted(grouped)
    minimum_coverage = min(coverages)
    maximum_coverage = max(coverages)

    if minimum_coverage == maximum_coverage:
        normalization = plt.Normalize( #type:ignore
            minimum_coverage - 1,
            maximum_coverage + 1,
        )
    else:
        normalization = plt.Normalize( #type:ignore
            minimum_coverage,
            maximum_coverage,
        )

    colormap = plt.colormaps["viridis"]

    figure, axis = plt.subplots(figsize=(9, 5))

    for coverage in coverages:
        steps = sorted(grouped[coverage])
        average_enemy_counts = [
            np.mean(grouped[coverage][step])
            for step in steps
        ]

        axis.plot(
            steps,
            average_enemy_counts,
            color=colormap(normalization(coverage)),
            label=f"{coverage:g}%",
        )

    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(
            norm=normalization,
            cmap=colormap,
        ),
        ax=axis,
    )
    colorbar.set_label("Obstacle coverage (%)")

    axis.set_title("Average enemy count over simulation steps")
    axis.set_xlabel("Timestep")
    axis.set_ylabel("Average number of enemies")
    axis.grid(alpha=0.3)

    figure.tight_layout()

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

def plot_dot_distribution(logs, value_name, title, y_label):
    grouped = defaultdict(list)

    for log in logs:
        version = get_config_value(log, "version")

        if version is None:
            continue

        label = VERSION_LABELS.get(version, f"Unknown ({version})")

        for state in log["states"]:
            value = state.get(value_name)

            if value is not None:
                grouped[label].append(value)

    if not grouped:
        return

    labels = [
        label for label in VERSION_LABELS.values()
        if label in grouped
    ]

    figure, axis = plt.subplots(figsize=(8, 5))
    rng = np.random.default_rng(42)

    for position, label in enumerate(labels, start=1):
        values = np.asarray(grouped[label], dtype=float)

        # Small horizontal jitter keeps individual measurements visible.
        x_values = position + rng.uniform(-0.08, 0.08, len(values))

        axis.scatter(
            x_values,
            values,
            alpha=0.35,
            s=14,
        )

        axis.scatter(
            [position],
            [np.mean(values)],
            color="red",
            marker="x",
            s=60,
            label="Mean" if position == 1 else None,
        )

    axis.set_title(title)
    axis.set_xlabel("A* implementation")
    axis.set_ylabel(y_label)
    axis.set_xticks(range(1, len(labels) + 1), labels)
    axis.grid(axis="y", alpha=0.3)
    axis.legend()

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
    )
    args = parser.parse_args()

    logs = load_logs(args.data_dir)

    if not logs:
        raise SystemExit(f"No JSONL logs found in {args.data_dir}")

    # plot_average_teleports_vs_coverage(logs)
    # plot_average_enemies_vs_timestep(logs)
    # plot_astar_performance(logs)
    # plot_time_per_path_step(logs)
    plot_dot_distribution(
        logs,
        "planner_time_ms",
        "A* execution time",
        "Execution time (ms)",
    )
    # plot_dot_distribution(logs, "path_length", "A* path lengths", "Path length")
    plot_astar_statistics(logs)
    plot_execution_time_with_stats(logs)
    plt.show()