"""Parser: turns tokens into a program made of scenes and statements."""

from .errors import ReelError

# Expression AST node kinds:
#   ("num", value) ("str", value) ("bool", value) ("name", name)
#   ("nothing",) ("list", [exprs]) ("call", name, [exprs], line)
#   ("length", expr) ("at", base, index)
#   ("bin", op, left, right) ("not", expr)
# Statement node kinds:
#   ("set", name, expr, line) ("say", expr, line)
#   ("if", cond, then_body, else_body, line)
#   ("repeat", count_expr, body, line)
#   ("while", cond, body, line) ("foreach", var, expr, body, line)
#   ("call", name, [exprs], line) ("giveback", expr, line) ("add", expr, name, line)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- token helpers ----------

    def peek(self):
        return self.tokens[self.pos]

    def next(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def at_word(self, word):
        t = self.peek()
        return t.kind == "WORD" and t.value == word

    def expect_word(self, word):
        t = self.next()
        if t.kind != "WORD" or t.value != word:
            raise self.error_here(f'I expected "{word}" but found {self.describe(t)} instead.')
        return t

    def skip_newlines(self):
        while self.peek().kind == "NEWLINE":
            self.next()

    def expect_newline(self):
        t = self.next()
        if t.kind == "NEWLINE" or t.kind == "EOF":
            return
        raise ReelError(t.line, f'I expected the line to end here but found {self.describe(t)}.')

    def describe(self, tok):
        if tok.kind == "EOF":
            return "the end of the file"
        if tok.kind == "NAME":
            return f'"{tok.value}"'
        if tok.kind == "STRING":
            return "some text"
        if tok.kind == "NUMBER":
            return str(tok.value)
        if tok.kind == "NEWLINE":
            return "the end of the line"
        return f'"{tok.value}"'

    def error_here(self, message):
        t = self.peek()
        return ReelError(t.line, message)

    # ---------- program & scenes ----------

    def parse_program(self):
        scenes = []
        self.skip_newlines()
        while self.peek().kind != "EOF":
            scenes.append(self.parse_scene())
            self.skip_newlines()
        return scenes

    def parse_scene(self):
        start = self.expect_word("SCENE")
        name_tok = self.next()
        if name_tok.kind != "NAME":
            raise ReelError(name_tok.line, 'After SCENE I need a name, like "SCENE main".')
        params = []
        if self.at_word("WITH"):
            self.next()
            params.append(self.expect_param_name())
            while self.peek().kind == "COMMA":
                self.next()
                params.append(self.expect_param_name())
        self.expect_newline()
        body = self.parse_statements(until={"CUT"})
        self.expect_word("CUT")
        self.expect_newline()
        return {"name": name_tok.value, "params": params, "body": body, "line": start.line}

    def expect_param_name(self):
        t = self.next()
        if t.kind != "NAME":
            raise ReelError(t.line, "After WITH I need input names, like: SCENE greet WITH name")
        return t.value

    def parse_statements(self, until):
        """Parse statements until one of the words in `until` (or EOF)."""
        body = []
        while True:
            self.skip_newlines()
            t = self.peek()
            if t.kind == "EOF":
                if "CUT" not in until:
                    raise ReelError(t.line, "I reached the end but I was still waiting for END.")
                return body
            if t.kind == "WORD" and t.value in until:
                return body
            if t.kind == "WORD" and t.value in ("OTHERWISE", "END", "CUT"):
                raise ReelError(
                    t.line,
                    f'I found "{t.value}" but I was not expecting it here. '
                    "Did a block forget its END?",
                )
            body.append(self.parse_statement())

    # ---------- statements ----------

    def parse_statement(self):
        t = self.peek()
        if t.kind != "WORD":
            raise ReelError(t.line, f'I do not know what to do with {self.describe(t)}.')
        if t.value == "SET":
            return self.parse_set()
        if t.value == "SAY":
            return self.parse_say()
        if t.value == "IF":
            return self.parse_if()
        if t.value == "REPEAT":
            return self.parse_repeat()
        if t.value == "WHILE":
            return self.parse_while()
        if t.value == "FOR":
            return self.parse_foreach()
        if t.value == "CALL":
            node = self.parse_call(stop={"NEWLINE", "EOF"})
            self.expect_newline()
            return node
        if t.value == "GIVE":
            return self.parse_giveback()
        if t.value == "ADD":
            return self.parse_add_statement()
        raise ReelError(
            t.line,
            f'I do not understand "{t.value}" here. '
            "Try SET, SAY, IF, REPEAT, WHILE, FOR EACH, CALL, GIVE BACK or ADD.",
        )

    def parse_set(self):
        start = self.expect_word("SET")
        name_tok = self.next()
        if name_tok.kind != "NAME":
            raise ReelError(name_tok.line, "After SET I need a name to store the value in.")
        self.expect_word("TO")
        expr = self.parse_expr(stop={"NEWLINE", "OTHERWISE", "END", "CUT", "EOF"})
        self.expect_newline()
        return ("set", name_tok.value, expr, start.line)

    def parse_say(self):
        start = self.expect_word("SAY")
        expr = self.parse_expr(stop={"NEWLINE", "OTHERWISE", "END", "CUT", "EOF"})
        self.expect_newline()
        return ("say", expr, start.line)

    def parse_if(self):
        start = self.expect_word("IF")
        cond = self.parse_expr(stop={"NEWLINE"})
        self.expect_newline()
        then_body = self.parse_statements(until={"OTHERWISE", "END"})
        else_body = []
        if self.at_word("OTHERWISE"):
            self.next()
            self.expect_newline()
            else_body = self.parse_statements(until={"END"})
        self.expect_word("END")
        self.expect_newline()
        return ("if", cond, then_body, else_body, start.line)

    def parse_repeat(self):
        start = self.expect_word("REPEAT")
        count = self.parse_expr(stop={"TIMES", "NEWLINE"})
        self.expect_word("TIMES")
        self.expect_newline()
        body = self.parse_statements(until={"END"})
        self.expect_word("END")
        self.expect_newline()
        return ("repeat", count, body, start.line)

    def parse_while(self):
        start = self.expect_word("WHILE")
        cond = self.parse_expr(stop={"NEWLINE"})
        self.expect_newline()
        body = self.parse_statements(until={"END"})
        self.expect_word("END")
        self.expect_newline()
        return ("while", cond, body, start.line)

    def parse_foreach(self):
        start = self.expect_word("FOR")
        self.expect_word("EACH")
        var_tok = self.next()
        if var_tok.kind != "NAME":
            raise ReelError(var_tok.line, "After FOR EACH I need a name for each item.")
        self.expect_word("IN")
        expr = self.parse_expr(stop={"NEWLINE"})
        self.expect_newline()
        body = self.parse_statements(until={"END"})
        self.expect_word("END")
        self.expect_newline()
        return ("foreach", var_tok.value, expr, body, start.line)

    def parse_call(self, stop):
        """Parse CALL name [WITH arg, arg, ...]. Returns a call node."""
        start = self.expect_word("CALL")
        name_tok = self.next()
        if name_tok.kind != "NAME":
            raise ReelError(name_tok.line, 'After CALL I need a scene name, like CALL greet WITH "Ann".')
        args = []
        if self.at_word("WITH"):
            self.next()
            while not self.at_stop(stop) and self.peek().kind != "RPAREN":
                args.append(self.parse_expr(stop))
                if self.peek().kind == "COMMA":
                    self.next()
                    continue
                break
        return ("call", name_tok.value, args, start.line)

    def parse_giveback(self):
        start = self.expect_word("GIVE")
        self.expect_word("BACK")
        expr = self.parse_expr(stop={"NEWLINE", "OTHERWISE", "END", "CUT", "EOF"})
        self.expect_newline()
        return ("giveback", expr, start.line)

    def parse_add_statement(self):
        start = self.expect_word("ADD")
        expr = self.parse_expr(stop={"TO", "NEWLINE", "EOF"})
        self.expect_word("TO")
        name_tok = self.next()
        if name_tok.kind != "NAME":
            raise ReelError(name_tok.line, "After ADD ... TO I need the name of a list.")
        self.expect_newline()
        return ("add", expr, name_tok.value, start.line)

    # ---------- expressions ----------
    # stop contains token *kinds* ("NEWLINE", "EOF") or WORD values ("TIMES", ...)

    def at_stop(self, stop):
        t = self.peek()
        if t.kind in stop:
            return True
        return t.kind == "WORD" and t.value in stop

    def parse_expr(self, stop):
        return self.parse_or(stop)

    def parse_or(self, stop):
        left = self.parse_and(stop)
        while self.at_word("OR") and "OR" not in stop:
            self.next()
            right = self.parse_and(stop)
            left = ("bin", "OR", left, right)
        return left

    def parse_and(self, stop):
        left = self.parse_not(stop)
        while self.at_word("AND") and "AND" not in stop:
            self.next()
            right = self.parse_not(stop)
            left = ("bin", "AND", left, right)
        return left

    def parse_not(self, stop):
        if self.at_word("NOT") and "NOT" not in stop:
            self.next()
            return ("not", self.parse_not(stop))
        return self.parse_compare(stop)

    def parse_compare(self, stop):
        left = self.parse_add(stop)
        ops = {
            "EQUALS": "==", "BIGGER": "BIG", "SMALLER": "SMALL",
        }
        while True:
            t = self.peek()
            if t.kind == "WORD" and t.value in ops and t.value not in stop:
                self.next()
                if t.value in ("BIGGER", "SMALLER"):
                    self.expect_word("THAN")
                right = self.parse_add(stop)
                left = ("bin", ops[t.value], left, right)
                continue
            return left

    def parse_add(self, stop):
        left = self.parse_mul(stop)
        while True:
            t = self.peek()
            if t.kind == "WORD" and t.value in ("PLUS", "MINUS", "JOIN") and t.value not in stop:
                self.next()
                right = self.parse_mul(stop)
                left = ("bin", t.value, left, right)
                continue
            return left

    def parse_mul(self, stop):
        left = self.parse_unary(stop)
        while True:
            t = self.peek()
            if t.kind == "WORD" and t.value in ("TIMES", "DIVIDED") and t.value not in stop:
                self.next()
                op = "TIMES"
                if t.value == "DIVIDED":
                    self.expect_word("BY")
                    op = "DIVIDED"
                right = self.parse_unary(stop)
                left = ("bin", op, left, right)
                continue
            return left

    def parse_unary(self, stop):
        if self.at_word("LENGTH") and "LENGTH" not in stop:
            start = self.next()
            self.expect_word("OF")
            operand = self.parse_unary(stop)
            return ("length", operand, start.line)
        node = self.parse_primary(stop)
        # postfix: cast AT 1
        while self.at_word("AT") and "AT" not in stop:
            self.next()
            index = self.parse_unary(stop)
            node = ("at", node, index)
        return node

    def parse_primary(self, stop):
        t = self.next()
        if t.kind == "NUMBER":
            return ("num", t.value)
        if t.kind == "STRING":
            return ("str", t.value)
        if t.kind == "NAME":
            return ("name", t.value)
        if t.kind == "LPAREN":
            expr = self.parse_expr(stop)
            closing = self.next()
            if closing.kind != "RPAREN":
                raise ReelError(closing.line, 'I opened a ( but never closed it with ).')
            return expr
        if t.kind == "WORD":
            if t.value == "YES":
                return ("bool", True)
            if t.value == "NO":
                return ("bool", False)
            if t.value == "NOTHING":
                return ("nothing",)
            if t.value == "LIST":
                return self.parse_list(stop)
            if t.value == "CALL":
                self.pos -= 1  # let parse_call consume CALL itself
                return self.parse_call(stop)
        raise ReelError(t.line, f'I do not understand {self.describe(t)} here.')

    def parse_list(self, stop):
        items = []
        while (
            not self.at_stop(stop)
            and self.peek().kind not in ("COMMA", "RPAREN")
        ):
            items.append(self.parse_expr(stop))
            if self.peek().kind == "COMMA":
                self.next()
                continue
            break
        # allow a trailing comma-free end; a comma right before the end is an error
        return ("list", items)


def parse(tokens):
    return Parser(tokens).parse_program()
