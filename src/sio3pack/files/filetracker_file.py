from sio3pack.files.file import File


class FiletrackerFile(File):
    """
    Base class for all files in a package that are tracked by filetracker.
    """

    def __init__(self, path: str):
        super().__init__(path)
        # TODO: should raise FileNotFoundError if file is not tracked
        raise NotImplementedError()
