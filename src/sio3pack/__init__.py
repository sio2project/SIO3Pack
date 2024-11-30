__version__ = "0.0.1"

from sio3pack.files.file import File
from sio3pack.packages.package import Package


def from_file(file: str | File, django_settings=None) -> Package:
    """
    Initialize a package object from a file (archive or directory).
    :param file: The file path or File object.
    :param django_settings: Django settings object.
    :return: The package object.
    """
    if isinstance(file, str):
        file = File(file)
    return Package.from_file(file, django_settings)
