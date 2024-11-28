from sio3pack.files.file import File


class LocalFile(File):
    """
    Base class for all files in a package that are stored locally.
    """

    def __init__(self, path: str):
        super().__init__(path)
