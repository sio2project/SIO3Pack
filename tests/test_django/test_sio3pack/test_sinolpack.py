import pytest

import sio3pack
from sio3pack.django.common.models import SIO3Package, SIO3PackMainModelSolution
from sio3pack.django.sinolpack.models import SinolpackAdditionalFile, SinolpackConfig, SinolpackModelSolution
from sio3pack.packages import Sinolpack
from tests.fixtures import Compression, PackageInfo, get_archived_package
from tests.utils import assert_contents_equal


def _save_and_test_simple(package_info: PackageInfo) -> tuple[Sinolpack, SIO3Package]:
    assert package_info.type == "sinolpack"
    package = sio3pack.from_file(package_info.path)
    assert isinstance(package, Sinolpack)
    package.save_to_db(1)
    assert SIO3Package.objects.filter(problem_id=1).exists()
    db_package = SIO3Package.objects.get(problem_id=1)
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

    model_solutions = package.model_solutions
    db_model_solutions = SinolpackModelSolution.objects.filter(package=db_package)
    assert len(model_solutions) == db_model_solutions.count()
    for order, msdict in enumerate(model_solutions):
        kind = msdict["kind"]
        solution = msdict["file"]
        ms = db_model_solutions.get(order_key=order)
        assert ms.name == solution.filename
        assert ms.kind == kind
        assert_contents_equal(ms.source_file.read().decode("utf-8"), solution.read())

    main_ms = package.main_model_solution
    assert main_ms is not None
    db_main_ms = SIO3PackMainModelSolution.objects.get(package=db_package)
    assert_contents_equal(db_main_ms.source_file.read().decode("utf-8"), main_ms.read())


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_additional_files(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, db_package = _save_and_test_simple(package_info)
    additional_files = package.additional_files
    db_additional_files = SinolpackAdditionalFile.objects.filter(package=db_package)
    assert db_additional_files.count() == 1
    assert len(additional_files) == db_additional_files.count()

    for file in additional_files:
        af = db_additional_files.get(name=file.filename)
        assert_contents_equal(af.file.read().decode("utf-8"), file.read())
        assert af.name == file.filename


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_from_db(get_archived_package):
    package_info: PackageInfo = get_archived_package()
    package, _ = _save_and_test_simple(package_info)
    package_from_db: Sinolpack = sio3pack.from_db(1)

    assert package.short_name == package_from_db.short_name
    assert package.full_name == package_from_db.full_name
    assert package.lang_titles == package_from_db.lang_titles
    assert package.config == package_from_db.config

    with pytest.raises(AttributeError):
        assert not hasattr(package_from_db, "non_existent_attribute")
        package_from_db.non_existent_attribute

    assert package_from_db.main_model_solution is not None
    assert_contents_equal(package_from_db.main_model_solution.read().decode("utf-8"), package.main_model_solution.read())
    assert False
