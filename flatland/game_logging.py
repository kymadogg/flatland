import json
from datetime import datetime
from pathlib import Path
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    "--test",
    type=str,
    default="default",
    help="Name of the test",
)
args = parser.parse_args()

test_name = args.test

timestamp = f"{datetime.now().strftime('%H:%M:%S')}_{datetime.now().strftime('%f')[:2]}"
LOG_FILE = Path(f"data/{test_name}/trial_{timestamp}.jsonl")

def _json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value

def _write(record):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        json.dump(record, file, default=_json_value)
        file.write("\n")

def log_config(args, hero, goal, enemies):
    _write({
        "type": "config",
        "config": vars(args).copy(),
        "hero_start": hero,
        "goal": goal,
        "enemies": enemies,
    })

def log_state(step, hero, goal, enemies, path, hero_cost, planner_time_ms):
    _write({
        "type": "state",
        "step": step,
        "hero": hero,
        "goal": goal,
        "enemies": enemies,
        "path_length": len(path) if path else 0,
        "hero_cost": hero_cost,
        "planner_time_ms": planner_time_ms,
    })

def log_result(result, step, teleport_count):
    _write({
        "type": "result",
        "result": result,
        "step": step,
        "teleports": teleport_count,
    })

