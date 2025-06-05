class SIO3PackException(Exception):
    """A wrapper for all exceptions raised by SIO3Pack."""

    def __init__(self, message, full_message=None):
        """
        Initialize the SIO3PackException.

        :param message: A short description of the error.
        :param full_message: A detailed description of the error, if available.
        """
        super().__init__(message)
        self.message = message
        self._full_message = full_message

    def _generate_full_message(self):
        """
        Generate a full message for the exception if not provided.
        """
        return None

    @property
    def full_message(self):
        if self._full_message is None:
            return self._generate_full_message()
        return self._full_message
