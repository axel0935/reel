class ReelError(Exception):
    """A friendly Reel error. Always carries a line number.

    `origin` is the file name when the error comes from an imported file
    (e.g. "maths.reel"); it is None for the main file.
    """

    def __init__(self, line, message, origin=None):
        self.line = line
        self.message = message
        self.origin = origin
        super().__init__(str(self))

    def __str__(self):
        prefix = f"{self.origin}, " if self.origin else ""
        return f"{prefix}Line {self.line}: {self.message}"
