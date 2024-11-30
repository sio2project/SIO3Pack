import os.path

import pytest

from tests.fixtures import package, package_archived, Compression, all_compressions


@pytest.mark.parametrize("package", ["simple"], indirect=True)
def test_simple(package):
    package_path, type = package
    assert type == "sinolpack"
    print(os.listdir(package_path))
    assert os.path.isdir(package_path)


@pytest.mark.parametrize("package_archived", [("simple", c) for c in all_compressions], indirect=True)
def test_archive(package_archived):
    package_path, type = package_archived
    assert type == "sinolpack"
    print(package_path)
    assert os.path.isfile(package_path)
