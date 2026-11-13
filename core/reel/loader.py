"""Loader: reads a Reel program, follows IMPORT lines, and merges scenes.

`load()` returns a flat list of scene dicts (the same shape the parser
produces), with name-clash and circular-import checks applied.
"""

import pathlib

from .errors import ReelError
from .lexer import lex
from .parser import parse
from .interpreter import BUILTIN_SCENE_NAMES

LIB_DIR = pathlib.Path(__file__).resolve().parent / "lib"


def load(source, safe=False, base_dir=None):
    """Load source code and everything it IMPORTs. Returns a list of scenes."""
    base = pathlib.Path(base_dir) if base_dir else pathlib.Path.cwd()
    scenes = {}
    _load_source(
        source,
        display=None,
        real_path=None,
        base=base,
        safe=safe,
        stack=[],
        loaded=set(),
        scenes=scenes,
        is_import=False,
    )
    return list(scenes.values())


def _load_source(source, display, real_path, base, safe, stack, loaded, scenes, is_import):
    if real_path is not None:
        stack = stack + [real_path]
    try:
        program = parse(lex(source))
    except ReelError as e:
        if e.origin is None and display:
            e.origin = display
        raise

    for imp in program["imports"]:
        _, kind, name, line = imp
        if kind == "lib":
            fpath = LIB_DIR / f"{name}.reel"
        else:
            if safe:
                raise ReelError(line, "Importing files is turned off here.")
            fpath = base / f"{name}.reel"
        real = fpath.resolve()
        if real in loaded:
            continue  # this file was already imported elsewhere
        if real in stack:
            raise ReelError(
                line,
                f'Circular import: "{name}" is already being loaded.',
                origin=display,
            )
        if not fpath.is_file():
            raise ReelError(
                line,
                f'I cannot find "{name}.reel". Did you IMPORT the right name?',
                origin=display,
            )
        try:
            text = fpath.read_text(encoding="utf-8")
        except OSError as e:
            raise ReelError(line, f'I cannot read "{name}.reel": {e}', origin=display)
        _load_source(
            text,
            display=fpath.name,
            real_path=real,
            base=fpath.parent,
            safe=safe,
            stack=stack,
            loaded=loaded,
            scenes=scenes,
            is_import=True,
        )
        loaded.add(real)

    for scene in program["scenes"]:
        scene["origin"] = display
        if is_import and scene["name"] == "main":
            continue  # an imported file's SCENE main is ignored
        _add_scene(scene, scenes)


def _add_scene(scene, scenes):
    name = scene["name"]
    origin = scene.get("origin")
    if name in BUILTIN_SCENE_NAMES:
        raise ReelError(
            scene["line"],
            f'The name "{name}" belongs to a built-in scene. Pick another name.',
            origin=origin,
        )
    if name in scenes:
        raise ReelError(
            scene["line"],
            f'Two scenes are both called "{name}".',
            origin=origin,
        )
    scenes[name] = scene
