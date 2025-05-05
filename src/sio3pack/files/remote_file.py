import os.path

from sio3pack.files.file import File


class RemoteFile(File):
    """
    Base class for a file that is tracked by filetracker.
    """

    def __init__(self, path: str):
        super().__init__(path)
        self.filename = os.path.basename(path)
