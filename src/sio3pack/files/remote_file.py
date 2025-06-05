import os.path

from sio3pack.files.file import File


class RemoteFile(File):
    """
    Class for a file that is tracked by filetracker.

    :param oioioi.filetracker.fields.FileField file: The file field from the filetracker.
    :param str filename: The name of the file.
    """

    try:
        from oioioi.filetracker.fields import FileField
    except ImportError:
        from django.db import models

        FileField = models.FileField

    def __init__(self, file: FileField):
        self.file = file
        super().__init__(file.name)
        self.filename = os.path.basename(file.name)

    def read(self):
        """
        Read the file.
        """
        return self.file.read()
