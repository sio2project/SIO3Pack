import os
from sio3pack import utils
from sio3pack.files.file import File
from sio3pack.packages.package import Package


class Sinolpack(Package):
    """
    Represents a OIOIOI's standard problem package.
    """

    @classmethod
    def identify(cls, file: File) -> bool:
        """
        Identifies whether file is a Sinolpack.

        :param file: File with package.
        :return: True when file is a Sinolpack, otherwise False.
        """
        if utils.is_archive(file):
            return utils.has_dir(file, "in") and utils.has_dir(file, "out")
        return os.path.exists(os.path.join(file, "in")) and os.path.exists(os.path.join(file, "out"))
