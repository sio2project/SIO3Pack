import importlib
from typing import Any

from sio3pack import LocalFile
from sio3pack.files import File
from sio3pack.graph import Graph, GraphOperation
from sio3pack.packages.exceptions import UnknownPackageType
from sio3pack.packages.package.handler import NoDjangoHandler
from sio3pack.test import Test
from sio3pack.utils.archive import Archive
from sio3pack.utils.classinit import RegisteredSubclassesBase

from sio3pack.exceptions import SIO3PackException


def wrap_exceptions(func):
    """Decorator to catch exceptions and re-raise them as SIO3PackException."""

    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SIO3PackException:
            raise # Do not wrap SIO3PackExceptions again
        except Exception as e:
            raise SIO3PackException(f"SIO3Pack raised an exception in {func.__name__} function.", e)

    return decorator


class Package(RegisteredSubclassesBase):
    """
    Base class for all packages.
    """

    abstract = True

    def __init__(self):
        super().__init__()

    @classmethod
    @wrap_exceptions
    def identify(cls, file: LocalFile):
        """
        Identify if the package is of this type.
        """
        raise NotImplementedError()

    @classmethod
    @wrap_exceptions
    def from_file(cls, file: LocalFile, django_settings=None):
        """
        Create a package from a file.
        """
        for subclass in cls.subclasses:
            if subclass.identify(file):
                package = subclass()
                package._from_file(file, django_settings)
                return package
        raise UnknownPackageType(file.path)

    def _from_file(self, file: LocalFile):
        self.file = file
        if isinstance(file, LocalFile):
            if Archive.is_archive(file.path):
                self.is_archive = True
            else:
                self.is_archive = False

    @classmethod
    @wrap_exceptions
    def identify_db(cls, problem_id: int):
        """
        Identify if the package is of this type. Should check if there
        is a package of this type in the database with the given problem_id.
        """
        raise NotImplementedError()

    @classmethod
    @wrap_exceptions
    def from_db(cls, problem_id: int):
        """
        Create a package from the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception. If there is no
        package with the given problem_id, it should raise an UnknownPackageType
        exception.
        """
        for subclass in cls.subclasses:
            if subclass.identify_db(problem_id):
                package = subclass()
                package._from_db(problem_id)
                return package
        raise UnknownPackageType(problem_id)

    def _from_db(self, problem_id: int):
        """
        Internal method to setup the package from the database. If sio3pack
        isn't installed with Django support, it should raise an ImproperlyConfigured
        exception.
        """
        self.problem_id = problem_id

    def _setup_django_handler(self, problem_id: int):
        try:
            import django

            self.django_enabled = True
            module_path, class_name = self.django_handler.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, class_name)
            self.django = handler(package=self, problem_id=problem_id)
        except ImportError:
            self.django_enabled = False
            self.django = NoDjangoHandler()

    @wrap_exceptions
    def get_task_id(self) -> str:
        pass

    @wrap_exceptions
    def get_titles(self) -> dict[str, str]:
        pass

    @wrap_exceptions
    def get_title(self, lang: str | None = None) -> str:
        pass

    @wrap_exceptions
    def get_statements(self) -> dict[str, File]:
        pass

    @wrap_exceptions
    def get_statement(self, lang: str | None = None) -> File:
        pass

    @wrap_exceptions
    def get_config(self) -> dict[str, Any]:
        pass

    @wrap_exceptions
    def get_tests(self) -> list[Test]:
        pass

    @wrap_exceptions
    def get_test(self, test_id: str) -> Test:
        pass

    @wrap_exceptions
    def get_unpack_graph(self) -> GraphOperation | None:
        pass

    @wrap_exceptions
    def get_run_graph(self, file: File, tests: list[Test] | None = None) -> GraphOperation | None:
        pass

    @wrap_exceptions
    def get_save_outs_graph(self, tests: list[Test] | None = None) -> GraphOperation | None:
        pass

    @wrap_exceptions
    def save_to_db(self, problem_id: int):
        """
        Save the package to the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception.
        """
        pass
