"""Built-in scenes (v0.3): chance, words, dates and files.

Each entry is a function (interp, args, line) -> value. `interp` gives
access to helpers like to_text/values_equal plus safe mode and base_dir.
"""

import datetime
import pathlib
import random
import re

from .errors import ReelError

MAX_FILE_SIZE = 1024 * 1024  # 1 MB
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# The "no value" marker, shared with the interpreter (imported from here
# so builtins never need to import the interpreter).
NOTHING = object()
WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


# ---------- small helpers ----------

def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _arity(name, args, count, line):
    if len(args) != count:
        raise ReelError(
            line,
            f'Scene "{name}" needs {count} input{"s" if count != 1 else ""} '
            f"but you gave {len(args)}.",
        )


def _num(name, value, line):
    if not _is_number(value):
        raise ReelError(line, f'"{name}" needs a number here.')
    return value


def _whole(name, value, line):
    value = _num(name, value, line)
    if value != int(value):
        raise ReelError(line, f'"{name}" needs a whole number, like 3, not 2.5.')
    return int(value)


def _text(name, value, line):
    if not isinstance(value, str):
        raise ReelError(line, f'"{name}" needs some text in quotes here.')
    return value


def _list(name, value, line):
    if not isinstance(value, list):
        raise ReelError(line, f'"{name}" needs a list here, like LIST "a", "b".')
    return value


def _date(name, value, line):
    text = _text(name, value, line)
    if not DATE_RE.match(text):
        raise ReelError(
            line,
            'That does not look like a date. Use the form "2026-11-13".',
        )
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        raise ReelError(
            line,
            f'"{text}" is not a real date. Check the day and month.',
        )


def _files_dir(interp):
    base = pathlib.Path(interp.base_dir) if interp.base_dir else pathlib.Path.cwd()
    return base / "reel_files"


def _file_path(interp, name, line):
    """Resolve a simple file name inside reel_files/, or raise a friendly error."""
    if (
        not isinstance(name, str)
        or not name
        or "/" in name
        or "\\" in name
        or ".." in name
        or pathlib.PurePath(name).is_absolute()
    ):
        raise ReelError(
            line,
            "File names must be simple: no /, no .., no full paths. "
            "Just something like \"notes.txt\".",
        )
    files_dir = _files_dir(interp)
    target = (files_dir / name).resolve()
    if target.parent != files_dir.resolve():
        raise ReelError(line, "That file name is not allowed here.")
    return target


def _no_files_in_safe_mode(interp, line):
    if interp.safe:
        raise ReelError(line, "Files are turned off here.")


# ---------- chance ----------

def b_random_between(interp, args, line):
    _arity("random_between", args, 2, line)
    low = _whole("random_between", args[0], line)
    high = _whole("random_between", args[1], line)
    if low > high:
        raise ReelError(line, "The first number must not be bigger than the second.")
    return random.randint(low, high)


def b_random_pick(interp, args, line):
    _arity("random_pick", args, 1, line)
    items = _list("random_pick", args[0], line)
    if not items:
        raise ReelError(line, "I cannot pick from an empty list.")
    return random.choice(items)


def b_shuffle(interp, args, line):
    _arity("shuffle", args, 1, line)
    items = list(_list("shuffle", args[0], line))
    random.shuffle(items)
    return items


# ---------- words ----------

def b_upper(interp, args, line):
    _arity("upper", args, 1, line)
    return _text("upper", args[0], line).upper()


def b_lower(interp, args, line):
    _arity("lower", args, 1, line)
    return _text("lower", args[0], line).lower()


def b_trim(interp, args, line):
    _arity("trim", args, 1, line)
    return _text("trim", args[0], line).strip()


def b_split(interp, args, line):
    _arity("split", args, 2, line)
    text = _text("split", args[0], line)
    sep = _text("split", args[1], line)
    if sep == "":
        raise ReelError(line, "The separator cannot be empty.")
    return text.split(sep)


def b_glue(interp, args, line):
    _arity("glue", args, 2, line)
    items = _list("glue", args[0], line)
    sep = _text("glue", args[1], line)
    return sep.join(interp.to_text(v) for v in items)


def b_replace(interp, args, line):
    _arity("replace", args, 3, line)
    text = _text("replace", args[0], line)
    old = _text("replace", args[1], line)
    new = _text("replace", args[2], line)
    return text.replace(old, new)


def b_contains(interp, args, line):
    _arity("contains", args, 2, line)
    haystack, needle = args
    if isinstance(haystack, list):
        return any(interp.values_equal(item, needle) for item in haystack)
    text = _text("contains", haystack, line)
    part = _text("contains", needle, line)
    return part in text


def b_starts_with(interp, args, line):
    _arity("starts_with", args, 2, line)
    text = _text("starts_with", args[0], line)
    part = _text("starts_with", args[1], line)
    return text.startswith(part)


def b_to_number(interp, args, line):
    _arity("to_number", args, 1, line)
    text = _text("to_number", args[0], line).strip()
    try:
        return float(text)
    except ValueError:
        raise ReelError(line, f'"{text}" is not a number.')


# ---------- dates ----------

def b_today(interp, args, line):
    _arity("today", args, 0, line)
    return datetime.date.today().isoformat()


def b_now(interp, args, line):
    _arity("now", args, 0, line)
    return datetime.datetime.now().strftime("%H:%M")


def b_days_between(interp, args, line):
    _arity("days_between", args, 2, line)
    d1 = _date("days_between", args[0], line)
    d2 = _date("days_between", args[1], line)
    return (d2 - d1).days


def b_add_days(interp, args, line):
    _arity("add_days", args, 2, line)
    d = _date("add_days", args[0], line)
    n = _whole("add_days", args[1], line)
    return (d + datetime.timedelta(days=n)).isoformat()


def b_weekday(interp, args, line):
    _arity("weekday", args, 1, line)
    d = _date("weekday", args[0], line)
    return WEEKDAYS[d.weekday()]


# ---------- files ----------

def b_read_file(interp, args, line):
    _arity("read_file", args, 1, line)
    _no_files_in_safe_mode(interp, line)
    target = _file_path(interp, args[0], line)
    if not target.is_file():
        raise ReelError(line, f'I cannot find the file "{args[0]}".')
    data = target.read_bytes()
    if len(data) > MAX_FILE_SIZE:
        raise ReelError(line, f'"{args[0]}" is bigger than 1 MB. Too heavy to read!')
    return data.decode("utf-8", errors="replace")


def b_read_lines(interp, args, line):
    _arity("read_lines", args, 1, line)
    text = b_read_file(interp, args, line)
    return text.splitlines()


def b_write_file(interp, args, line):
    _arity("write_file", args, 2, line)
    _no_files_in_safe_mode(interp, line)
    target = _file_path(interp, args[0], line)
    content = interp.to_text(args[1])
    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ReelError(line, "That is bigger than 1 MB. Too heavy to write!")
    _files_dir(interp).mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return NOTHING


def b_append_file(interp, args, line):
    _arity("append_file", args, 2, line)
    _no_files_in_safe_mode(interp, line)
    target = _file_path(interp, args[0], line)
    content = interp.to_text(args[1])
    if target.is_file() and target.stat().st_size + len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ReelError(line, "That is bigger than 1 MB. Too heavy to write!")
    _files_dir(interp).mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(content)
    return NOTHING


def b_file_exists(interp, args, line):
    _arity("file_exists", args, 1, line)
    _no_files_in_safe_mode(interp, line)
    target = _file_path(interp, args[0], line)
    return target.is_file()


# name -> function
BUILTIN_SCENES = {
    # chance
    "random_between": b_random_between,
    "random_pick": b_random_pick,
    "shuffle": b_shuffle,
    # words
    "upper": b_upper,
    "lower": b_lower,
    "trim": b_trim,
    "split": b_split,
    "glue": b_glue,
    "replace": b_replace,
    "contains": b_contains,
    "starts_with": b_starts_with,
    "to_number": b_to_number,
    # dates
    "today": b_today,
    "now": b_now,
    "days_between": b_days_between,
    "add_days": b_add_days,
    "weekday": b_weekday,
    # files
    "read_file": b_read_file,
    "read_lines": b_read_lines,
    "write_file": b_write_file,
    "append_file": b_append_file,
    "file_exists": b_file_exists,
}
