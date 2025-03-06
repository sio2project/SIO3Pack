class SIO3PackException(Exception):
    """A wrapper for all exceptions raised by SIO3Pack."""

    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception
