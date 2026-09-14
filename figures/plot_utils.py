import json

VERSION_LABELS = {
    "py": "Python",
    "rs": "Rust"
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
