"""Lexer: turns Reel source code into a list of tokens."""

from .errors import ReelError

KEYWORDS = {
    "SCENE", "SET", "TO", "SAY", "IF", "OTHERWISE", "END", "REPEAT",
    "TIMES", "CUT", "PLUS", "MINUS", "DIVIDED", "BY", "JOIN",
    "EQUALS", "BIGGER", "THAN", "SMALLER", "AND", "OR", "NOT", "YES", "NO",
    # v0.2
    "WITH", "CALL", "GIVE", "BACK", "NOTHING", "LIST", "ADD", "AT",
    "LENGTH", "OF", "FOR", "EACH", "IN", "WHILE",
}


class Token:
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind = kind      # "NUMBER", "STRING", "NAME", "WORD", "NEWLINE", "LPAREN", "RPAREN", "EOF"
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.kind}, {self.value!r}, line {self.line})"


def lex(source):
    tokens = []
    lines = source.split("\n")
    for lineno, raw in enumerate(lines, start=1):
        line = _strip_comment(raw)
        tokens.extend(_lex_line(line, lineno))
    tokens.append(Token("EOF", None, len(lines)))
    return tokens


def _strip_comment(line):
    in_string = False
    i = 0
    while i < len(line) - 1:
        ch = line[i]
        if ch == '"':
            in_string = not in_string
        elif not in_string and ch == "-" and line[i + 1] == "-":
            return line[:i]
        i += 1
    return line


def _lex_line(line, lineno):
    tokens = []
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if ch in " \t\r":
            i += 1
            continue
        if ch == ",":
            tokens.append(Token("COMMA", ",", lineno))
            i += 1
            continue
        if ch == "(":
            tokens.append(Token("LPAREN", "(", lineno))
            i += 1
            continue
        if ch == ")":
            tokens.append(Token("RPAREN", ")", lineno))
            i += 1
            continue
        if ch == '"':
            i += 1
            chars = []
            while i < n and line[i] != '"':
                if line[i] == "\\" and i + 1 < n:
                    nxt = line[i + 1]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                    i += 2
                else:
                    chars.append(line[i])
                    i += 1
            if i >= n:
                raise ReelError(lineno, 'I found a " but never the closing one. Did you forget it?')
            i += 1  # skip closing quote
            tokens.append(Token("STRING", "".join(chars), lineno))
            continue
        if ch.isdigit():
            j = i
            while j < n and (line[j].isdigit() or line[j] == "."):
                j += 1
            text = line[i:j]
            if text.count(".") > 1:
                raise ReelError(lineno, f'I do not understand the number "{text}".')
            tokens.append(Token("NUMBER", float(text), lineno))
            i = j
            continue
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (line[j].isalnum() or line[j] == "_"):
                j += 1
            word = line[i:j]
            if word in KEYWORDS:
                tokens.append(Token("WORD", word, lineno))
            elif word == word.upper() and word != word.lower():
                tokens.append(Token("WORD", word, lineno))  # UNKNOWN UPPERCASE WORD
            elif word == word.lower() or word.replace("_", "").isalnum():
                if any(c.isupper() for c in word):
                    raise ReelError(
                        lineno,
                        f'"{word}" is not a valid name. Names use only lowercase letters, digits and _.',
                    )
                tokens.append(Token("NAME", word, lineno))
            else:
                raise ReelError(lineno, f'I do not understand the word "{word}".')
            i = j
            continue
        raise ReelError(lineno, f'I do not understand the character "{ch}".')
    if tokens:
        tokens.append(Token("NEWLINE", "\n", lineno))
    return tokens
