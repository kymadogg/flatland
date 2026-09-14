import subprocess
import notify2
import time

PER_LOOP = 100
LOOPS = 3
locked_seed = True

notify2.init('Flatland')

def run_program(command):
    process = subprocess.run(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )

    if process.returncode != 0:
        print(process.stderr)

start_time = time.perf_counter()

for loop_index in range(LOOPS):
    for trial_index in range(PER_LOOP):
        command = [
            "uv", "run", "python", "-m", "flatland.main", "--headless",
            "--frames", "1000", 
            "-v", f"{loop_index}", 
            "-ms", "1"
        ]

        if locked_seed:
            command.extend(["-r", f"{trial_index}"])

        run_program(command)
        print(
            f"trial={trial_index + 1}/{PER_LOOP}"
        )

elapsed = (time.perf_counter() - start_time)
n = notify2.Notification("Test Complete",
                         f"{PER_LOOP * LOOPS} trials took {elapsed}.",
                         "notification-message-im")

n.show()