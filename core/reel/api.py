"""Public API for Reel. Tests and the playground only use run()."""

from .lexer import lex
from .parser import parse
from .interpreter import interpret
from .errors import ReelError


def run(source: str) -> dict:
    """Run Reel source code.

    Returns {"output": str, "error": str or None}.
    """
    try:
        tokens = lex(source)
        scenes = parse(tokens)
        output = interpret(scenes)
        return {"output": output, "error": None}
    except ReelError as e:
        return {"output": "", "error": str(e)}
    except Exception as e:  # never crash the caller; stay friendly
        return {"output": "", "error": f"Something went wrong: {e}"}
