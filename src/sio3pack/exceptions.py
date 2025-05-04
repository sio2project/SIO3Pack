import traceback


class SIO3PackException(Exception):
    """A wrapper for all exceptions raised by SIO3Pack."""

    def __init__(self, message, original_exception):
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception.__class__.__name__
        self.traceback = traceback.format_exc()

    def __str__(self):
        return f"{self.message}\nOriginal exception: {self.original_exception}\nTraceback:\n{self.traceback}"