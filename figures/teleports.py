from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import sys

if "--headless" in sys.argv:
    matplotlib.use("Agg")

from plot_utils import VERSION_LABELS, get_config_value, read_log, load_logs

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