import os

from sio3pack.files.file import File


class LocalFile(File):
    """
    Base class for all files in a package that are stored locally.
    """

    @classmethod
    def get_file_matching_extension(cls, dir: str, filename: str, extensions: list[str]) -> "LocalFile":
        """
        Get the file with the given filename and one of the given extensions.
        :param dir: The directory to search in.
        :param filename: The filename.
        :param extensions: The extensions.
        :return: The file object.
        """
        for ext in extensions:
            path = os.path.join(dir, filename + "." + ext)
            if os.path.exists(path):
                return cls(path)
        raise FileNotFoundError

    def __init__(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError
        super().__init__(path)
        self.filename = os.path.basename(path)

    def read(self) -> str:
        with open(self.path, "r") as f:
            return f.read()

    def write(self, text: str):
        with open(self.path, "w") as f:
            f.write(text)
