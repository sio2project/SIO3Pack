from tests.fixtures import PackageInfo
from sio3pack import Package
from sio3pack.packages import Sinolpack


def common_checks(package_info: PackageInfo, package: Package):
    assert package_info.type == "sinolpack"
    assert isinstance(package, Sinolpack)
    assert package.short_name == package_info.task_id
