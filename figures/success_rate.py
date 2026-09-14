from collections import defaultdict
from pathlib import Path
import argparse
import sys
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

if "--headless" in sys.argv:
    matplotlib.use("Agg")

from plot_utils import VERSION_LABELS, load_logs, get_config_value


def plot_success_rate_vs_coverage(logs):
    grouped = defaultdict(lambda: defaultdict(list))

    for log in logs:
        coverage = get_config_value(log, "coverage")
        version = get_config_value(log, "version")
        result = log["result"]

        if (
            coverage is None
            or version is None
            or result is None
        ):
            continue

        success = result.get("success")

        if success is None:
            continue

        label = VERSION_LABELS.get(
            version,
            f"Unknown ({version})",
        )

        grouped[label][coverage].append(
            bool(success)
        )

    if not grouped:
        return

    figure, axis = plt.subplots(figsize=(8, 5))

    labels = [
        label
        for label in VERSION_LABELS.values()
        if label in grouped
    ]

    for label in labels:
        coverages = sorted(grouped[label])

        success_rates = [
            np.mean(grouped[label][coverage]) * 100
            for coverage in coverages
        ]

        axis.plot(
            coverages,
            success_rates,
            marker="o",
            label=label,
        )

    axis.set_title("A* success rate vs obstacle coverage")
    axis.set_xlabel("Obstacle coverage (%)")
    axis.set_ylabel("Success rate (%)")
    axis.set_ylim(0, 100)
    axis.grid(alpha=0.3)
    axis.legend()

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

    plot_success_rate_vs_coverage(logs)