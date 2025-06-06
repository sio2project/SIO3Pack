class SIO3PackException(Exception):
    """
    A base class for all custom exceptions raised by SIO3Pack.

    :param str message: A short description of the error.
    :param str full_message: A detailed description of the error, if available.
    """

    def __init__(self, message: str, full_message: str = None):
        """
        Initialize the SIO3PackException.

        :param str message: A short description of the error.
        :param str full_message: A detailed description of the error, if available.
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
