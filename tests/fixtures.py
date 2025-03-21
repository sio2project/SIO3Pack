import importlib.util
import os.path
import shutil
import tarfile
import tempfile
import zipfile
from enum import Enum

import pytest


class Compression(Enum):
    NONE = ""
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    TGZ = "tgz"


all_compressions = [c.value for c in Compression if c != Compression.NONE]


class PackageInfo:
    def __init__(self, path, type, task_id, compression):
        self.path = path
        self.type = type
        self.task_id = task_id
        self.compression = compression

    def is_archive(self):
        return self.compression != Compression.NONE


def _tar_archive(dir, dest, compression=None):
    """
    Create a tar archive of the specified directory.
    """
    if compression is None:
        mode = "w"
    else:
        mode = f"w:{compression}"
    with tarfile.open(dest, mode) as tar:
        tar.add(dir, arcname=os.path.basename(dir))


def _zip_archive(dir, dest):
    """
    Create a zip archive of the specified directory.
    """
    with zipfile.ZipFile(dest, "w") as zip:
        for root, dirs, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(os.path.basename(dir), os.path.relpath(file_path, dir))
                zip.write(file_path, arcname)


def _create_package(package_name, tmpdir, archive=False, extension=Compression.ZIP):
    packages = os.path.join(os.path.dirname(__file__), "test_packages")
    if not os.path.exists(os.path.join(packages, package_name)):
        raise FileNotFoundError(f"Package {package_name} does not exist")

    spec = importlib.util.spec_from_file_location(package_name, os.path.join(packages, package_name, "__init__.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    task_id = module.TASK_ID
    type = module.TYPE
    package_path = os.path.join(tmpdir.name, task_id)
    shutil.copytree(os.path.join(packages, package_name), package_path, ignore=shutil.ignore_patterns("__pycache__"))
    os.unlink(os.path.join(package_path, "__init__.py"))

    if archive:
        if extension == Compression.ZIP:
            _zip_archive(package_path, os.path.join(tmpdir.name, f"{task_id}.zip"))
        elif extension == Compression.TAR_GZ or extension == Compression.TGZ:
            _tar_archive(package_path, os.path.join(tmpdir.name, f"{task_id}.{extension.value}"), "gz")
        else:
            raise ValueError(f"Unknown extension {extension}")
        package_path = os.path.join(tmpdir.name, f"{task_id}.{extension.value}")

    return PackageInfo(
        path=package_path,
        type=type,
        task_id=task_id,
        compression=extension,
    )


@pytest.fixture
def get_package(request):
    """
    Fixture to create a temporary directory with specified package.
    """
    package_name = request.param
    tmpdir = tempfile.TemporaryDirectory()
    package_info = _create_package(package_name, tmpdir)

    yield lambda: package_info

    tmpdir.cleanup()


@pytest.fixture
def get_archived_package(request):
    """
    Fixture to create a temporary directory with specified package, but archived.
    """
    package_name, extension = request.param
    archive = extension != Compression.NONE
    tmpdir = tempfile.TemporaryDirectory()
    package_info = _create_package(package_name, tmpdir, archive, extension)

    yield lambda: package_info

    tmpdir.cleanup()
