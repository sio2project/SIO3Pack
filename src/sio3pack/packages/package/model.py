from typing import Any

from sio3pack.files.file import File
from sio3pack.graph.graph import Graph
from sio3pack.test.test import Test

from sio3pack.packages import all_packages

class Package:
    """
    Base class for all packages.
    """

    def __init__(self):
        pass

    @classmethod
    def from_file(cls, file: File):
        for package_type in all_packages:
            if package_type.identify(file):
                return package_type(file)

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
