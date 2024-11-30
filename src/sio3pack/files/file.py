class File:
    """
    Base class for all files in a package.
    """

    def __init__(self, path: str):
        self.path = path

    def __str__(self):
        return f"<{self.__class__.__name__} {self.path}>"

    def read(self) -> str:
        raise NotImplementedError()

    def write(self, text: str):
        raise NotImplementedError()
