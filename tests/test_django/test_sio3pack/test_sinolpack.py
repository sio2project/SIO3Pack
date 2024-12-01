import pytest

import sio3pack
from sio3pack.packages import Sinolpack
from sio3pack.django.sinolpack.models import SinolpackPackage
from tests.fixtures import Compression, get_archived_package, PackageInfo


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_simple(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    assert package_info.type == "sinolpack"
    package = sio3pack.from_file(package_info.path)
    assert isinstance(package, Sinolpack)
    package.save_to_db(1)
    assert SinolpackPackage.objects.filter(problem_id=1).exists()
    db_package = SinolpackPackage.objects.get(problem_id=1)
    assert db_package.short_name == package.short_name

    with pytest.raises(sio3pack.PackageAlreadyExists):
        package.save_to_db(1)
