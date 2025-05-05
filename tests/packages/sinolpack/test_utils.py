import pytest

import sio3pack
from sio3pack.packages import Sinolpack
from sio3pack.packages.sinolpack import constants
from sio3pack.test import Test
from tests.fixtures import PackageInfo, get_package

@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_get_test_id(get_package):
    package_info: PackageInfo = get_package()
    package: Sinolpack = sio3pack.from_file(package_info.path)

    assert package.get_test_id_from_filename("abc1a.in") == "1a"
    assert package.get_test_id_from_filename("abc0.in") == "0"
    assert package.get_test_id_from_filename("abc1a.out") == "1a"
    assert package.get_test_id_from_filename("abc10.in") == "10"
    assert package.get_test_id_from_filename("abc10abc.in") == "10abc"
    assert package.get_test_id_from_filename("abc10abc20.in") == "10abc20"
    try:
        assert package.get_test_id_from_filename("abcdef.in") == "def"
    except ValueError:
        pass


@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_get_group(get_package):
    package_info: PackageInfo = get_package()
    package: Sinolpack = sio3pack.from_file(package_info.path)

    assert package.get_group_from_filename("abc1a.in") == "1"
    assert package.get_group_from_filename("abc0.in") == "0"
    assert package.get_group_from_filename("abc1a.out") == "1"
    assert package.get_group_from_filename("abc10.in") == "10"
    assert package.get_group_from_filename("abc10abc.in") == "10"
    assert package.get_group_from_filename("abc10abc20.in") == "10"
    try:
        assert package.get_group_from_filename("abcdef.in") == "def"
    except ValueError:
        pass


@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_get_corresponding_out(get_package):
    package_info: PackageInfo = get_package()
    package: Sinolpack = sio3pack.from_file(package_info.path)

    assert package.get_corresponding_out_filename("abc1a.in") == "abc1a.out"
    assert package.get_corresponding_out_filename("abc0.in") == "abc0.out"
    assert package.get_corresponding_out_filename("abc1a.out") == "abc1a.out"
    assert package.get_corresponding_out_filename("abc10.in") == "abc10.out"
    assert package.get_corresponding_out_filename("abc10abc.in") == "abc10abc.out"
    assert package.get_corresponding_out_filename("abc10abc20.in") == "abc10abc20.out"


@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_get_limits(get_package):
    package_info: PackageInfo = get_package()
    package: Sinolpack = sio3pack.from_file(package_info.path)

    package.config = {
        "time_limit": 1000,
        "memory_limit": 1024,
        "time_limits": {
            "1": 2000,
            "1a": 3000,
        },
        "memory_limits": {
            "1": 2048,
            "1a": 3072,
        },
        "override_limits": {
            "py": {
                "time_limit": 5000,
                "memory_limit": 4096,
                "time_limits": {
                    "2": 6000,
                    "2a": 7000,
                },
                "memory_limits": {
                    "2": 4096,
                    "2a": 5120,
                }
            }
        }
    }

    def get_for_test(type: str, test_name: str, lang: str = "cpp"):
        test_id = package.get_test_id_from_filename(test_name)
        group = package.get_group_from_filename(test_name)
        test = Test(test_name, test_id, None, None, group)
        if type == "time":
            return package.get_time_limit_for_test(test, lang)
        else:
            return package.get_memory_limit_for_test(test, lang)

    # Test time limits
    assert get_for_test("time", "abc0a.in") == 1000
    assert get_for_test("time", "abc1b.in") == 2000
    assert get_for_test("time", "abc1a.in") == 3000
    assert get_for_test("time", "abc2.in", "cpp") == 1000
    assert get_for_test("time", "abc1.in", "py") == 5000
    assert get_for_test("time", "abc2b.in", "py") == 6000
    assert get_for_test("time", "abc2a.in", "py") == 7000

    # Test memory limits
    assert get_for_test("memory", "abc0a.in") == 1024
    assert get_for_test("memory", "abc1b.in") == 2048
    assert get_for_test("memory", "abc1a.in") == 3072
    assert get_for_test("memory", "abc2.in", "cpp") == 1024
    assert get_for_test("memory", "abc1.in", "py") == 4096
    assert get_for_test("memory", "abc2b.in", "py") == 4096
    assert get_for_test("memory", "abc2a.in", "py") == 5120

    # Test default limits
    package.config = {}
    assert get_for_test("time", "abc0a.in") == constants.DEFAULT_TIME_LIMIT
    assert get_for_test("time", "abc1b.in") == constants.DEFAULT_TIME_LIMIT
    assert get_for_test("memory", "abc0.in") == constants.DEFAULT_MEMORY_LIMIT
    assert get_for_test("memory", "abc1b.in") == constants.DEFAULT_MEMORY_LIMIT
