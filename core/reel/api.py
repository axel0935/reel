"""Public API for Reel. Tests and the playground only use run()."""

from .loader import load
from .interpreter import interpret
from .errors import ReelError


def run(source: str, safe: bool = False, base_dir=None) -> dict:
    """Run Reel source code.

    safe=True turns off file functions and IMPORT "name" (IMPORT LIB still
    works). base_dir is the folder used to find imported files and
    reel_files/.

    Returns {"output": str, "error": str or None}.
    """
    try:
        scenes = load(source, safe=safe, base_dir=base_dir)
        output = interpret(scenes, safe=safe, base_dir=base_dir)
        return {"output": output, "error": None}
    except ReelError as e:
        return {"output": "", "error": str(e)}
    except Exception as e:  # never crash the caller; stay friendly
        return {"output": "", "error": f"Something went wrong: {e}"}
