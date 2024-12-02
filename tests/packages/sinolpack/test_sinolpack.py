import os.path

import pytest

import sio3pack
from sio3pack.packages import Sinolpack
from tests.fixtures import Compression, PackageInfo, all_compressions, get_archived_package, get_package


@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_from_file(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    assert package_info.type == "sinolpack"
    package = sio3pack.from_file(package_info.path)
    assert isinstance(package, Sinolpack)
    assert package.short_name == package_info.task_id
    if package_info.is_archive():
        assert package.is_archive
    else:
        assert package.rootdir == package_info.path


@pytest.mark.no_django
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_no_django(get_package):
    package_info: PackageInfo = get_package()
    with pytest.raises(sio3pack.ImproperlyConfigured):
        sio3pack.from_db(1)

    package = sio3pack.from_file(package_info.path)
    with pytest.raises(sio3pack.ImproperlyConfigured):
        package.save_to_db(1)
