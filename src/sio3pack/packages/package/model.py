import importlib
from typing import Any

from sio3pack.exceptions import SIO3PackException
from sio3pack.files import File, LocalFile
from sio3pack.packages.exceptions import UnknownPackageType
from sio3pack.packages.package.handler import NoDjangoHandler
from sio3pack.test import Test
from sio3pack.utils.archive import Archive
from sio3pack.utils.classinit import RegisteredSubclassesBase
from sio3pack.workflow import Workflow, WorkflowOperation


def wrap_exceptions(func):
    """Decorator to catch exceptions and re-raise them as SIO3PackException."""

    def decorator(*args, **kwargs):
        return func(*args, **kwargs)
        # try:
        #     return func(*args, **kwargs)
        # except SIO3PackException:
        #     raise  # Do not wrap SIO3PackExceptions again
        # except Exception as e:
        #     raise SIO3PackException(f"SIO3Pack raised an exception in {func.__name__} function.", e)

    return decorator


class Package(RegisteredSubclassesBase):
    """
    Base class for all packages.

    :param str short_name: Short name of the problem.
    :param str full_name: Full name of the problem.
    :param dict[str, str] lang_titles: A dictionary of problem titles,
        where keys are language codes and values are titles.
    :param dict[str, File] lang_statements: A dictionary of problem
        statements, where keys are language codes and values are files.
    :param dict[str, Any] config: Configuration of the problem.
    :param list[tuple[ModelSolutionKind, File]] model_solutions: A list
        of model solutions, where each element is a tuple containing
        a model solution kind and a file.
    :param list[File] additional_files: A list of additional files for
        the problem.
    :param list[File] attachments: A list of attachments related to the problem.
    :param WorkflowManager workflow_manager: A workflow manager for the problem.
    """

    abstract = True

    def __init__(self):
        super().__init__()
        self.django = None

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

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self.django, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @wrap_exceptions
    def get_title(self, lang: str | None = None) -> str:
        pass

    @wrap_exceptions
    def get_statement(self, lang: str | None = None) -> File | None:
        pass

    @wrap_exceptions
    def get_tests(self) -> list[Test]:
        pass

    @wrap_exceptions
    def get_test(self, test_id: str) -> Test:
        pass

    def has_test_gen(self) -> bool:
        """
        Check if the package has test generation.
        """
        return False

    def has_verify(self) -> bool:
        """
        Check if the package has verification.
        """
        return False

    @wrap_exceptions
    def get_unpack_graph(self, return_func: callable = None) -> WorkflowOperation | None:
        return self.workflow_manager.get_unpack_operation(self.has_test_gen(), self.has_verify(), return_func)

    @wrap_exceptions
    def get_run_graph(self, file: File, tests: list[Test] | None = None) -> WorkflowOperation | None:
        pass

    @wrap_exceptions
    def get_save_outs_graph(self, tests: list[Test] | None = None) -> WorkflowOperation | None:
        pass

    @wrap_exceptions
    def save_to_db(self, problem_id: int):
        """
        Save the package to the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception.
        """
        pass
