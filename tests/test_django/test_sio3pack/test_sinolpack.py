import pytest

import sio3pack
from sio3pack.django.sinolpack.models import (SinolpackAdditionalFile,
                                              SinolpackConfig,
                                              SinolpackModelSolution,
                                              SinolpackPackage,)
from sio3pack.packages import Sinolpack
from tests.fixtures import Compression, PackageInfo, get_archived_package
from tests.utils import assert_contents_equal


def _save_and_test_simple(package_info: PackageInfo) -> tuple[Sinolpack, SinolpackPackage]:
    assert package_info.type == "sinolpack"
    package = sio3pack.from_file(package_info.path)
    assert isinstance(package, Sinolpack)
    package.save_to_db(1)
    assert SinolpackPackage.objects.filter(problem_id=1).exists()
    db_package = SinolpackPackage.objects.get(problem_id=1)
    assert db_package.short_name == package.short_name
    return package, db_package


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_simple(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, db_package = _save_and_test_simple(package_info)

    assert package.get_title() == db_package.full_name

    with pytest.raises(sio3pack.PackageAlreadyExists):
        package.save_to_db(1)


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_config(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, db_package = _save_and_test_simple(package_info)
    config = SinolpackConfig.objects.get(package=db_package)
    assert package.config == config.parsed_config


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_translated_titles(get_archived_package):
    pytest.skip("Not implemented")


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_model_solutions(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, db_package = _save_and_test_simple(package_info)

    model_solutions = package.get_model_solutions()
    db_model_solutions = SinolpackModelSolution.objects.filter(package=db_package)
    assert len(model_solutions) == db_model_solutions.count()
    for order, (kind, solution) in enumerate(model_solutions):
        ms = db_model_solutions.get(order_key=order)
        assert ms.name == solution.filename
        assert ms.kind == kind
        assert_contents_equal(ms.source_file.read().decode("utf-8"), solution.read())


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_additional_files(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, db_package = _save_and_test_simple(package_info)
    additional_files = package.get_additional_files()
    db_additional_files = SinolpackAdditionalFile.objects.filter(package=db_package)
    assert db_additional_files.count() == 1
    assert len(additional_files) == db_additional_files.count()

    for file in additional_files:
        af = db_additional_files.get(name=file.filename)
        assert_contents_equal(af.file.read().decode("utf-8"), file.read())
        assert af.name == file.filename
