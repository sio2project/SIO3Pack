from sio3pack.files import File


class RemoteFile(File):
    """
    Base class for a file that is tracked by filetracker.
    """

    def __init__(self, path: str):
        super().__init__(path)
        # TODO: should raise FileNotFoundError if file is not tracked
        raise NotImplementedError()
