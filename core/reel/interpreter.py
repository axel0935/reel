"""Interpreter: runs a parsed program and returns the printed output."""

from .errors import ReelError


class Interpreter:
    def __init__(self, scenes):
        self.scenes = {s["name"]: s["body"] for s in scenes}
        self.vars = {}
        self.output_lines = []

    def run(self):
        if "main" not in self.scenes:
            raise ReelError(1, 'I cannot find "SCENE main". Every Reel program needs one.')
        self.exec_block(self.scenes["main"], 1)
        return "\n".join(self.output_lines) + ("\n" if self.output_lines else "")

    def exec_block(self, body, line):
        for stmt in body:
            kind = stmt[0]
            if kind == "set":
                _, name, expr, sline = stmt
                self.vars[name] = self.eval(expr, sline)
            elif kind == "say":
                _, expr, sline = stmt
                self.output_lines.append(self.to_text(self.eval(expr, sline)))
            elif kind == "if":
                _, cond, then_body, else_body, sline = stmt
                if self.truthy(self.eval(cond, sline)):
                    self.exec_block(then_body, sline)
                else:
                    self.exec_block(else_body, sline)
            elif kind == "repeat":
                _, count_expr, rep_body, sline = stmt
                count = self.eval(count_expr, sline)
                if not isinstance(count, (int, float)) or isinstance(count, bool):
                    raise ReelError(sline, "REPEAT needs a number, like REPEAT 3 TIMES.")
                if count != int(count):
                    raise ReelError(sline, "REPEAT needs a whole number, like 3, not 2.5.")
                for _ in range(int(count)):
                    self.exec_block(rep_body, sline)
            else:
                raise ReelError(line, f"I do not know how to run {kind}.")

    # ---------- expressions ----------

    def eval(self, node, line):
        kind = node[0]
        if kind == "num":
            return node[1]
        if kind == "str":
            return node[1]
        if kind == "bool":
            return node[1]
        if kind == "name":
            name = node[1]
            if name not in self.vars:
                raise ReelError(line, f'I don\'t know "{name}". Did you SET it first?')
            return self.vars[name]
        if kind == "not":
            return not self.truthy(self.eval(node[1], line))
        if kind == "bin":
            return self.eval_bin(node, line)
        raise ReelError(line, "Something inside the expression went wrong.")

    def eval_bin(self, node, line):
        _, op, left_node, right_node = node
        # AND / OR short-circuit
        if op == "AND":
            return self.truthy(self.eval(left_node, line)) and self.truthy(self.eval(right_node, line))
        if op == "OR":
            return self.truthy(self.eval(left_node, line)) or self.truthy(self.eval(right_node, line))

        left = self.eval(left_node, line)
        right = self.eval(right_node, line)

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

    # ---------- helpers ----------

    def truthy(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        return bool(value)

    def require_numbers(self, left, right, line):
        if not _is_number(left) or not _is_number(right):
            raise ReelError(line, "Math (PLUS, MINUS, TIMES, DIVIDED BY) works only on numbers.")

    def values_equal(self, a, b):
        if _is_number(a) and _is_number(b):
            return a == b
        return type(a) is type(b) and a == b

    def to_text(self, value):
        if isinstance(value, bool):
            return "YES" if value else "NO"
        if _is_number(value):
            if float(value).is_integer():
                return str(int(value))
            return str(value)
        return str(value)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def interpret(scenes):
    return Interpreter(scenes).run()
