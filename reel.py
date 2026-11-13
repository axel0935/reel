#!/usr/bin/env python3
"""Reel command line: python3 reel.py run [--safe] <file.reel>"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "core"))

from reel.api import run  # noqa: E402


def main(argv):
    if len(argv) < 3 or argv[1] != "run":
        print("Usage: python3 reel.py run [--safe] <file.reel>", file=sys.stderr)
        return 2
    safe = "--safe" in argv[2:]
    files = [a for a in argv[2:] if a != "--safe"]
    if not files:
        print("Usage: python3 reel.py run [--safe] <file.reel>", file=sys.stderr)
        return 2
    path = files[0]
    try:
        source = pathlib.Path(path).read_text(encoding="utf-8")
    except OSError as e:
        print(f"I cannot open \"{path}\": {e}", file=sys.stderr)
        return 1
    base_dir = str(pathlib.Path(path).resolve().parent)
    result = run(source, safe=safe, base_dir=base_dir)
    if result["error"] is not None:
        print(result["error"], file=sys.stderr)
        return 1
    sys.stdout.write(result["output"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
