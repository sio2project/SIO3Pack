__version__ = "1.0.0.dev3"

from sio3pack.files import LocalFile
from sio3pack.packages.exceptions import *
from sio3pack.packages.package import Package

__all__ = ["from_file", "from_db"]

from sio3pack.packages.package.configuration import SIO3PackConfig


def from_file(file: str | LocalFile, configuration: SIO3PackConfig = None) -> Package:
    """
    Initialize a package object from a file (archive or directory).

    :param file: The file path or File object.
    :param configuration: Configration of the package.
    :return: The package object.
    """
    if isinstance(file, str):
        file = LocalFile(file)
    return Package.from_file(file, configuration=configuration)


def from_db(problem_id: int, configuration: SIO3PackConfig = None) -> Package:
    """
    Initialize a package object from the database.
    If sio3pack isn't installed with Django support, it should raise an ImproperlyConfigured exception.
    If there is no package with the given problem_id, it should raise an UnknownPackageType exception.

    :param problem_id: The problem id.
    :param configuration: Configuration of the package.
    :return: The package object.
    """
    try:
        from django.conf import settings

        configuration = configuration or SIO3PackConfig()
        configuration.django_settings = settings
        return Package.from_db(problem_id, configuration)
    except ImportError:
        raise ImproperlyConfigured("sio3pack is not installed with Django support.")
