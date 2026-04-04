import subprocess
import json
from config import KRAKEN_CLI_PATH


def get_paper_status():
    raw = subprocess.check_output(
        [KRAKEN_CLI_PATH, "paper", "status", "-o", "json"],
        timeout=10,
        stderr=subprocess.DEVNULL,
    )
    return json.loads(raw)
