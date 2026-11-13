"""Subprocess runner for Reel code.

Reads Reel source from stdin, executes it using run(source) from core/reel/api.py,
and writes the JSON result to stdout.
"""

import json
from pathlib import Path
import sys

# Locate project root and core directory
PLAYGROUND_DIR = Path(__file__).resolve().parent
ROOT_DIR = PLAYGROUND_DIR.parent
CORE_DIR = ROOT_DIR / "core"

if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

try:
    from reel.api import run
except Exception as err:
    def run(source: str) -> dict:
        return {"output": "", "error": f"Failed to load Reel engine: {err}"}


def main():
    try:
        source = sys.stdin.read()
        result = run(source)
    except Exception as err:
        result = {"output": "", "error": f"Execution failed: {err}"}
    sys.stdout.write(json.dumps(result))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
