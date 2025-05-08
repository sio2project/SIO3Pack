import importlib
import os
from typing import Any, Type

from sio3pack.exceptions import SIO3PackException
from sio3pack.files import File, LocalFile
from sio3pack.packages.exceptions import ImproperlyConfigured, UnknownPackageType
from sio3pack.packages.package.configuration import SIO3PackConfig
from sio3pack.packages.package.handler import NoDjangoHandler
from sio3pack.test import Test
from sio3pack.utils.archive import Archive
from sio3pack.utils.classinit import RegisteredSubclassesBase
from sio3pack.workflow import WorkflowManager, WorkflowOperation


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
    :param bool is_from_db: If True, the package is created from the database.
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
    def from_file(cls, file: LocalFile, configuration=None):
        """
        Create a package from a file.
        """
        for subclass in cls.subclasses:
            if subclass.identify(file):
                package = subclass()
                package._from_file(file, configuration)
                return package
        raise UnknownPackageType(file.path)

    def _from_file(self, file: LocalFile, configuration=None):
        self.file = file
        self.configuration = configuration or SIO3PackConfig()
        self.is_from_db = False
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
    def from_db(cls, problem_id: int, configuration: SIO3PackConfig = None):
        """
        Create a package from the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception. If there is no
        package with the given problem_id, it should raise an UnknownPackageType
        exception.
        """
        for subclass in cls.subclasses:
            if subclass.identify_db(problem_id):
                package = subclass()
                package._from_db(problem_id, configuration)
                return package
        raise UnknownPackageType(problem_id)

    def _from_db(self, problem_id: int, configuration: SIO3PackConfig = None):
        """
        Internal method to setup the package from the database. If sio3pack
        isn't installed with Django support, it should raise an ImproperlyConfigured
        exception.
        """
        self.is_from_db = True
        self.problem_id = problem_id
        self.configuration = configuration or SIO3PackConfig()

    def _get_from_django_settings(self, key: str, default=None):
        if self.configuration.django_settings is None:
            return default
        if isinstance(self.configuration.django_settings, dict):
            return self.configuration.django_settings.get(key, default)
        return getattr(self.configuration.django_settings, key, default)

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

    def _setup_workflows_from_db(self):
        """
        Set up the workflows from the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception.
        """
        if not self.django_enabled:
            raise ImproperlyConfigured("Django is not enabled.")
        cls = self._workflow_manager_class()
        self.workflow_manager = cls(self, self.django.workflows)

    def _workflow_manager_class(self) -> Type[WorkflowManager]:
        return WorkflowManager

    def _default_workflow_manager(self) -> WorkflowManager:
        cls = self._workflow_manager_class()
        return cls(self, {})

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
    def get_unpack_operation(self, return_func: callable = None) -> WorkflowOperation | None:
        return self.workflow_manager.get_unpack_operation(self.has_test_gen(), self.has_verify(), return_func)

    def get_run_operation(
        self, program: File, tests: list[Test] | None = None, return_func: callable = None
    ) -> WorkflowOperation | None:
        """
        Get the run graph for the package. If the package doesn't have a
        run graph, it should return None.
        """
        return self.workflow_manager.get_run_operation(program, tests, return_func)

    def get_user_out_operation(
        self, program: File, test: Test, return_func: callable = None
    ) -> WorkflowOperation | None:
        """
        Get the workflow for getting the user's output for a given test.
        """
        return self.workflow_manager.get_user_out_operation(program, test, return_func)

    def get_test_run_operation(
        self, program: File, test: File, return_func: callable = None
    ) -> WorkflowOperation | None:
        """
        Get the workflow for running a test run. This means that
        the user can provide a test and the program, and the workflow will
        run the program with the test.
        """
        return self.workflow_manager.get_test_run_operation(program, test, return_func)

    def get_executable_path(self, program: File | str) -> str | None:
        """
        Get the executable path for a given program.
        """
        if self.is_from_db:
            return self.django.get_executable_path(program)
        else:
            if isinstance(program, File):
                assert isinstance(program, LocalFile)
                return os.path.join(self.file.path, ".cache", "executables", program.filename + ".e")
            else:
                return os.path.join(self.file.path, ".cache", "executables", os.path.basename(program) + ".e")

    def _get_compiler_full_name(self, lang: str) -> str:
        """
        Get the compiler for the package.
        """
        if lang in self.configuration.compilers_config:
            return self.configuration.compilers_config[lang].full_name
        else:
            raise KeyError(f"Compiler for language '{lang}' not found in configuration.")

    def _get_compiler_path(self, lang: str) -> str:
        """
        Get the compiler path for the package.
        """
        if lang in self.configuration.compilers_config:
            return self.configuration.compilers_config[lang].path
        else:
            raise KeyError(f"Compiler for language '{lang}' not found in configuration.")

    def _get_compiler_flags(self, lang: str) -> list[str]:
        """
        Get the compiler flags for the package.
        """
        if lang in self.configuration.compilers_config:
            return self.configuration.compilers_config[lang].flags
        else:
            raise KeyError(f"Compiler for language '{lang}' not found in configuration.")

    def get_cpp_compiler_full_name(self) -> str:
        """
        Get the C++ compiler for the package.
        """
        return self._get_compiler_full_name("cpp")

    def get_cpp_compiler_path(self) -> str:
        """
        Get the C++ compiler path for the package.
        """
        return self._get_compiler_path("cpp")

    def get_cpp_compiler_flags(self) -> list[str]:
        """
        Get the C++ compiler flags for the package.
        """
        return self._get_compiler_flags("cpp")

    def get_python_compiler_full_name(self) -> str:
        """
        Get the Python compiler for the package.
        """
        return self._get_compiler_full_name("python")

    def get_python_compiler_path(self) -> str:
        """
        Get the Python compiler path for the package.
        """
        return self._get_compiler_path("python")

    def get_python_compiler_flags(self) -> list[str]:
        """
        Get the Python compiler flags for the package.
        """
        return self._get_compiler_flags("python")

    def get_file_language(self, file: File | str) -> str:
        """
        Returns the language of the given file.
        """
        if isinstance(file, File):
            file = file.path
        ext = os.path.splitext(os.path.basename(file))[1]
        if ext in self.configuration.extensions_config:
            return self.configuration.extensions_config[ext]
        else:
            raise SIO3PackException(f"Unknown file extension '{ext}' for file '{file}'")

    @wrap_exceptions
    def save_to_db(self, problem_id: int):
        """
        Save the package to the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception.
        """
        pass

    def get_time_limit_for_test(self, test: Test) -> int:
        """
        Get the time limit for a given test.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def get_memory_limit_for_test(self, test: Test) -> int:
        """
        Get the memory limit for a given test.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")
