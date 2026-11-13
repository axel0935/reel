class ReelError(Exception):
    """A friendly Reel error. Always carries a line number."""

    def __init__(self, line, message):
        self.line = line
        self.message = message
        super().__init__(f"Line {line}: {message}")

    def __str__(self):
        return f"Line {self.line}: {self.message}"
