from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
import argparse
import matplotlib
import sys

if "--headless" in sys.argv:
    matplotlib.use("Agg")

from plot_utils import get_config_value, read_log, load_logs

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

def plot_enemy_distance_vs_timestep(logs):
    distance_by_step = defaultdict(list)
    enemy_count_by_step = defaultdict(list)

    for log in logs:
        for state in log["states"]:
            if (
                "step" not in state
                or "hero" not in state
                or "enemies" not in state
            ):
                continue

            step = state["step"]
            hero = state["hero"]
            enemies = state["enemies"]

            if not enemies:
                continue

            hero_row, hero_col = hero

            distances = []

            for enemy in enemies:
                enemy_row, enemy_col = enemy

                distance = np.sqrt(
                    (enemy_row - hero_row) ** 2
                    + (enemy_col - hero_col) ** 2
                )

                distances.append(distance)

            distance_by_step[step].append(
                np.mean(distances)
            )

            enemy_count_by_step[step].append(
                len(enemies)
            )

    if not distance_by_step:
        return

    steps = sorted(distance_by_step)

    average_distances = [
        np.mean(distance_by_step[step])
        for step in steps
    ]

    average_enemy_counts = [
        np.mean(enemy_count_by_step[step])
        for step in steps
    ]

    figure, axis = plt.subplots(figsize=(9, 5))

    minimum_count = min(average_enemy_counts)
    maximum_count = max(average_enemy_counts)

    if minimum_count == maximum_count:
        normalization = Normalize(
            minimum_count - 1,
            maximum_count + 1,
        )
    else:
        normalization = Normalize(
            minimum_count,
            maximum_count,
        )

    colormap = plt.colormaps["viridis"]

    for i in range(len(steps) - 1):
        axis.plot(
            steps[i:i + 2],
            average_distances[i:i + 2],
            color=colormap(
                normalization(average_enemy_counts[i])
            ),
        )

    axis.set_title("Average enemy distance from hero")
    axis.set_xlabel("Timestep")
    axis.set_ylabel("Average distance from hero (cells)")
    axis.grid(alpha=0.3)

    colorbar = figure.colorbar(
        plt.cm.ScalarMappable(
            norm=normalization,
            cmap=colormap,
        ),
        ax=axis,
    )
    colorbar.set_label("Average number of enemies")

    figure.tight_layout()

    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/cov_5_30"),
    )
    args = parser.parse_args()

    logs = load_logs(args.data_dir)

    if not logs:
        raise SystemExit(
            f"No JSONL logs found in {args.data_dir}"
        )

    plot_enemy_distance_vs_timestep(logs)