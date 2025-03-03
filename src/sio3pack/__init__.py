__version__ = "1.0.0.dev1"

from sio3pack.files import LocalFile
from sio3pack.packages.exceptions import ImproperlyConfigured, PackageAlreadyExists
from sio3pack.packages.package import Package


def from_file(file: str | LocalFile, django_settings=None) -> Package:
    """
    Initialize a package object from a file (archive or directory).
    :param file: The file path or File object.
    :param django_settings: Django settings object.
    :return: The package object.
    """
    if isinstance(file, str):
        file = LocalFile(file)
    return Package.from_file(file, django_settings=django_settings)


def from_db(problem_id: int) -> Package:
    """
    Initialize a package object from the database.
    If sio3pack isn't installed with Django support, it should raise an ImproperlyConfigured exception.
    If there is no package with the given problem_id, it should raise an UnknownPackageType exception.
    :param problem_id: The problem id.
    :return: The package object.
    """
    try:
        import django

        return Package.from_db(problem_id)
    except ImportError:
        raise ImproperlyConfigured("sio3pack is not installed with Django support.")
