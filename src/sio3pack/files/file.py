class File:
    """
    Base class for all files in a package.

    :param str path: The path to the file.
    """

    def __init__(self, path: str):
        self.path = path

    def __str__(self):
        return f"<{self.__class__.__name__} {self.path}>"

    def read(self) -> str:
        """
        Read the file content.

        :return: The content of the file.
        """
        raise NotImplementedError()

    def write(self, text: str):
        """
        Write to the file.

        :param str text: The text to write.
        """
        raise NotImplementedError()
