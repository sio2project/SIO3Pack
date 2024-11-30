from typing import Any

from sio3pack import LocalFile
from sio3pack.files import File
from sio3pack.graph import Graph
from sio3pack.packages.exceptions import UnknownPackageType
from sio3pack.test import Test
from sio3pack.utils.archive import Archive
from sio3pack.utils.classinit import RegisteredSubclassesBase


class Package(RegisteredSubclassesBase):
    """
    Base class for all packages.
    """

    abstract = True

    def __init__(self, file: File):
        super().__init__()
        self.file = file
        if isinstance(file, LocalFile):
            if Archive.is_archive(file.path):
                self.is_archive = True
            else:
                self.is_archive = False

    @classmethod
    def from_file(cls, file: LocalFile, django_settings=None):
        for subclass in cls.subclasses:
            if subclass.identify(file):
                return subclass(file, django_settings)
        raise UnknownPackageType(file.path)

    def get_task_id(self) -> str:
        pass

    def get_titles(self) -> dict[str, str]:
        pass

    def get_title(self, lang: str | None = None) -> str:
        pass

    def get_statements(self) -> dict[str, File]:
        pass

    def get_statement(self, lang: str | None = None) -> File:
        pass

    def get_config(self) -> dict[str, Any]:
        pass

    def get_tests(self) -> list[Test]:
        pass

    def get_test(self, test_id: str) -> Test:
        pass

    def get_package_graph(self) -> Graph:
        pass

    def get_run_graph(self, file: File, tests: list[Test] | None = None) -> Graph:
        pass

    def get_save_outs_graph(self, tests: list[Test] | None = None) -> Graph:
        pass
