import os

from sio3pack.files.file import File


class LocalFile(File):
    """
    Base class for a file in a package that is stored locally.
    """

    @classmethod
    def get_file_matching_extension(cls, dir: str, filename: str, extensions: list[str]) -> "LocalFile":
        """
        Get the file with the given filename and one of the given extensions.

        :param str dir: The directory to search in.
        :param str filename: The filename.
        :param list[str] extensions: The extensions.
        :return LocalFile: The file object.
        :raises FileNotFoundError: If no file is found.
        """
        for ext in extensions:
            path = os.path.join(dir, filename + "." + ext)
            if os.path.exists(path):
                return cls(path)
        raise FileNotFoundError

    def __init__(self, path: str, exists=True):
        """
        Initialize the file.

        :param str path: The path to the file.
        :param bool exists: If True, check if the file exists.
        :raises FileNotFoundError: If the file doesn't exist.
        """
        if not os.path.exists(path) and exists:
            raise FileNotFoundError
        super().__init__(path)
        self.filename = os.path.basename(path)

    def read(self) -> str:
        with open(self.path, "r") as f:
            return f.read()

    def write(self, text: str):
        with open(self.path, "w") as f:
            f.write(text)
