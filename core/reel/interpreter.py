"""Interpreter: runs a parsed program and returns the printed output."""

from .errors import ReelError
from .builtins import BUILTIN_SCENES, NOTHING

MAX_CALL_DEPTH = 100
MAX_WHILE_TURNS = 100000

# Names owned by built-in scenes (CALL random_between ... etc.).
# The loader uses this to reject user scenes with these names.
BUILTIN_SCENE_NAMES = frozenset(BUILTIN_SCENES)


class _ReturnSignal(Exception):
    """GIVE BACK jumps out of a scene with a value."""

    def __init__(self, value, line):
        self.value = value
        self.line = line


class Interpreter:
    def __init__(self, scenes, safe=False, base_dir=None):
        self.scenes = {s["name"]: s for s in scenes}
        self.vars = {}          # main scene's variables
        self.output_lines = []
        self.call_depth = 0
        self.safe = safe                  # safe mode: no file access (v0.3)
        self.base_dir = base_dir          # folder for reel_files/ and IMPORTs

    def run(self):
        if "main" not in self.scenes:
            raise ReelError(1, 'I cannot find "SCENE main". Every Reel program needs one.')
        main = self.scenes["main"]
        try:
            self.exec_block(main["body"], self.vars, main["line"])
        except _ReturnSignal:
            pass  # GIVE BACK in main simply ends the show
        except ReelError as e:
            if e.origin is None:
                e.origin = main.get("origin")
            raise
        return "\n".join(self.output_lines) + ("\n" if self.output_lines else "")

    # ---------- statements ----------

    def exec_block(self, body, frame, line):
        for stmt in body:
            kind = stmt[0]
            if kind == "set":
                _, name, expr, sline = stmt
                frame[name] = self.eval(expr, frame, sline)
            elif kind == "say":
                _, expr, sline = stmt
                self.output_lines.append(self.to_text(self.eval(expr, frame, sline)))
            elif kind == "if":
                _, cond, then_body, else_body, sline = stmt
                if self.truthy(self.eval(cond, frame, sline)):
                    self.exec_block(then_body, frame, sline)
                else:
                    self.exec_block(else_body, frame, sline)
            elif kind == "repeat":
                _, count_expr, rep_body, sline = stmt
                count = self.eval(count_expr, frame, sline)
                if not _is_number(count):
                    raise ReelError(sline, "REPEAT needs a number, like REPEAT 3 TIMES.")
                if count != int(count):
                    raise ReelError(sline, "REPEAT needs a whole number, like 3, not 2.5.")
                for _ in range(int(count)):
                    self.exec_block(rep_body, frame, sline)
            elif kind == "while":
                _, cond, while_body, sline = stmt
                turns = 0
                while self.truthy(self.eval(cond, frame, sline)):
                    turns += 1
                    if turns > MAX_WHILE_TURNS:
                        raise ReelError(sline, "This loop never ends.")
                    self.exec_block(while_body, frame, sline)
            elif kind == "foreach":
                _, var, expr, for_body, sline = stmt
                items = self.eval(expr, frame, sline)
                if not isinstance(items, list):
                    raise ReelError(sline, "FOR EACH needs a list to walk through.")
                for item in items:
                    frame[var] = item
                    self.exec_block(for_body, frame, sline)
            elif kind == "call":
                self.eval(stmt, frame, stmt[3])  # value is thrown away
            elif kind == "giveback":
                _, expr, sline = stmt
                raise _ReturnSignal(self.eval(expr, frame, sline), sline)
            elif kind == "add":
                _, expr, name, sline = stmt
                value = self.eval(expr, frame, sline)
                if name not in frame:
                    raise ReelError(sline, f'I don\'t know "{name}". Did you SET it first?')
                target = frame[name]
                if not isinstance(target, list):
                    raise ReelError(sline, f'"{name}" is not a list, so I cannot ADD to it.')
                target.append(value)
            else:
                raise ReelError(line, f"I do not know how to run {kind}.")

    # ---------- expressions ----------

    def eval(self, node, frame, line):
        kind = node[0]
        if kind == "num":
            return node[1]
        if kind == "str":
            return node[1]
        if kind == "bool":
            return node[1]
        if kind == "nothing":
            return NOTHING
        if kind == "name":
            name = node[1]
            if name not in frame:
                raise ReelError(line, f'I don\'t know "{name}". Did you SET it first?')
            return frame[name]
        if kind == "list":
            return [self.eval(item, frame, line) for item in node[1]]
        if kind == "length":
            value = self.eval(node[1], frame, line)
            if isinstance(value, list):
                return len(value)
            if isinstance(value, str):
                return len(value)
            raise ReelError(line, "LENGTH OF only works on lists and text.")
        if kind == "at":
            base = self.eval(node[1], frame, line)
            index = self.eval(node[2], frame, line)
            if not isinstance(base, list):
                raise ReelError(line, "AT only works on lists, like cast AT 1.")
            if not _is_number(index) or index != int(index):
                raise ReelError(line, "AT needs a whole number, like 1.")
            i = int(index)
            if i < 1 or i > len(base):
                raise ReelError(
                    line,
                    f'That list has {len(base)} item{"s" if len(base) != 1 else ""}, '
                    f"so there is no item {i}.",
                )
            return base[i - 1]
        if kind == "call":
            _, name, arg_exprs, _ = node
            args = [self.eval(a, frame, line) for a in arg_exprs]
            return self.call_scene(name, args, line)
        if kind == "not":
            return not self.truthy(self.eval(node[1], frame, line))
        if kind == "bin":
            return self.eval_bin(node, frame, line)
        raise ReelError(line, "Something inside the expression went wrong.")

    def eval_bin(self, node, frame, line):
        _, op, left_node, right_node = node
        if op == "AND":
            return self.truthy(self.eval(left_node, frame, line)) and self.truthy(
                self.eval(right_node, frame, line)
            )
        if op == "OR":
            return self.truthy(self.eval(left_node, frame, line)) or self.truthy(
                self.eval(right_node, frame, line)
            )

        left = self.eval(left_node, frame, line)
        right = self.eval(right_node, frame, line)

        if op == "PLUS":
            self.require_numbers(left, right, line)
            return left + right
        if op == "MINUS":
            self.require_numbers(left, right, line)
            return left - right
        if op == "TIMES":
            self.require_numbers(left, right, line)
            return left * right
        if op == "DIVIDED":
            self.require_numbers(left, right, line)
            if right == 0:
                raise ReelError(line, "I cannot divide by zero. Pick a bigger number!")
            return left / right
        if op == "JOIN":
            return self.to_text(left) + self.to_text(right)
        if op == "==":
            return self.values_equal(left, right)
        if op == "BIG":
            self.require_numbers(left, right, line)
            return left > right
        if op == "SMALL":
            self.require_numbers(left, right, line)
            return left < right
        raise ReelError(line, f'I do not understand the operator "{op}".')

    # ---------- scenes ----------

    def call_scene(self, name, args, line):
        builtin = BUILTIN_SCENES.get(name)
        if builtin is not None:
            return builtin(self, args, line)
        scene = self.scenes.get(name)
        if scene is None:
            raise ReelError(line, f'I do not know a scene called "{name}".')
        params = scene["params"]
        if len(args) != len(params):
            need = len(params)
            raise ReelError(
                line,
                f'Scene "{name}" needs {need} input{"s" if need != 1 else ""} '
                f"but you gave {len(args)}.",
            )
        if self.call_depth >= MAX_CALL_DEPTH:
            raise ReelError(
                line,
                "This scene is calling itself too many times. "
                "Is something stuck in a loop?",
            )
        frame = dict(zip(params, args))
        self.call_depth += 1
        try:
            self.exec_block(scene["body"], frame, scene["line"])
        except _ReturnSignal as ret:
            return ret.value
        except ReelError as e:
            if e.origin is None:
                e.origin = scene.get("origin")
            raise
        finally:
            self.call_depth -= 1
        return NOTHING

    # ---------- helpers ----------

    def truthy(self, value):
        if value is NOTHING:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, list):
            return len(value) > 0
        return bool(value)

    def require_numbers(self, left, right, line):
        if not _is_number(left) or not _is_number(right):
            raise ReelError(line, "Math (PLUS, MINUS, TIMES, DIVIDED BY) works only on numbers.")

    def values_equal(self, a, b):
        if _is_number(a) and _is_number(b):
            return a == b
        if a is NOTHING or b is NOTHING:
            return a is NOTHING and b is NOTHING
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(
                self.values_equal(x, y) for x, y in zip(a, b)
            )
        return type(a) is type(b) and a == b

    def to_text(self, value):
        if value is NOTHING:
            return "NOTHING"
        if isinstance(value, bool):
            return "YES" if value else "NO"
        if _is_number(value):
            if float(value).is_integer():
                return str(int(value))
            return str(value)
        if isinstance(value, list):
            return "[" + ", ".join(self.to_text(v) for v in value) + "]"
        return str(value)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def interpret(scenes, safe=False, base_dir=None):
    return Interpreter(scenes, safe=safe, base_dir=base_dir).run()
