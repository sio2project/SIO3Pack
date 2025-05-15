import pytest

import sio3pack
from sio3pack import LocalFile, SIO3PackConfig
from sio3pack.django.common.models import SIO3Package, SIO3PackMainModelSolution
from sio3pack.django.sinolpack.models import (
    SinolpackAdditionalFile,
    SinolpackConfig,
    SinolpackModelSolution,
    SinolpackSpecialFile,
)
from sio3pack.packages import Sinolpack
from tests.fixtures import Compression, PackageInfo, get_archived_package, get_package
from tests.utils import assert_contents_equal


def _save_and_test_simple(package_info: PackageInfo, config: SIO3PackConfig = None) -> tuple[Sinolpack, SIO3Package]:
    assert package_info.type == "sinolpack"
    package = sio3pack.from_file(package_info.path, config)
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
    assert db_additional_files.count() == 2
    assert len(additional_files) == db_additional_files.count()

    for file in additional_files:
        af = db_additional_files.get(name=file.filename)
        assert_contents_equal(af.file.read().decode("utf-8"), file.read())
        assert af.name == file.filename


@pytest.mark.django_db
@pytest.mark.parametrize("get_archived_package", [("simple", c) for c in Compression], indirect=True)
def test_from_db(get_archived_package):
    config = SIO3PackConfig(django_settings={"LANGUAGES": [("en", "English"), ("pl", "Polski")]})
    package_info: PackageInfo = get_archived_package()
    package, _ = _save_and_test_simple(package_info, config)
    package_from_db: Sinolpack = sio3pack.from_db(1)

    assert package.short_name == package_from_db.short_name
    assert package.full_name == package_from_db.full_name
    assert package.lang_titles == package_from_db.lang_titles
    assert package.config == package_from_db.config

    for lang in package.lang_titles.keys():
        assert package.get_title(lang) == package_from_db.get_title(lang)

    with pytest.raises(AttributeError):
        assert not hasattr(package_from_db, "non_existent_attribute")
        package_from_db.non_existent_attribute

    assert package_from_db.main_model_solution is not None
    assert_contents_equal(
        package_from_db.main_model_solution.read().decode("utf-8"), package.main_model_solution.read()
    )


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_model_solutions_from_db(get_package):
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info)
    from_db: Sinolpack = sio3pack.from_db(1)

    model_solutions = {}
    for ms in package.model_solutions:
        model_solutions[ms["file"].filename] = ms

    for ms in from_db.model_solutions:
        filename = ms["file"].filename
        assert filename in model_solutions
        assert_contents_equal(ms["file"].read().decode("utf-8"), model_solutions[filename]["file"].read())
        assert ms["kind"] == model_solutions[filename]["kind"]


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_config_from_db(get_package):
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info)
    from_db: Sinolpack = sio3pack.from_db(1)

    assert package.config == from_db.config


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_additional_files_from_db(get_package):
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info)
    from_db: Sinolpack = sio3pack.from_db(1)

    additional_files: list[LocalFile] = package.additional_files
    assert type(additional_files[0]) == LocalFile
    db_additional_files = SinolpackAdditionalFile.objects.filter(package=from_db.db_package)
    assert len(additional_files) == db_additional_files.count()

    for file in additional_files:
        print(file.filename)
        af = db_additional_files.get(name=file.filename)
        print(af)
        assert_contents_equal(af.file.read().decode("utf-8"), file.read())
        assert af.name == file.filename


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_special_files_from_db(get_package):
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info)
    from_db: Sinolpack = sio3pack.from_db(1)

    special_files = package.special_files
    db_special_files = from_db.special_files
    assert set(db_special_files.keys()) == set(special_files.keys())

    for type, file in special_files.items():
        if file is not None:
            assert type in db_special_files

            assert SinolpackSpecialFile.objects.filter(
                package=from_db.db_package,
                type=type,
            ).exists()

            additional_file = SinolpackAdditionalFile.objects.get(
                package=from_db.db_package,
                name=file.filename,
            )
            assert_contents_equal(file.read(), additional_file.file.read())
        else:
            assert db_special_files[type] is None


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_titles_from_db(get_package):
    config = SIO3PackConfig(django_settings={"LANGUAGES": [("en", "English"), ("pl", "Polski")]})
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info, config)
    from_db: Sinolpack = sio3pack.from_db(1, config)

    assert package.short_name == from_db.short_name
    assert package.full_name == from_db.full_name
    assert "pl" in package.lang_titles
    assert package.lang_titles == from_db.lang_titles


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_statements_from_db(get_package):
    config = SIO3PackConfig(django_settings={"LANGUAGES": [("en", "English"), ("pl", "Polski")]})
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info, config)
    from_db: Sinolpack = sio3pack.from_db(1, config)

    assert set(package.lang_statements.keys()) == set(from_db.lang_statements.keys())
    for lang, statement in package.lang_statements.items():
        assert lang in from_db.lang_statements
        assert_contents_equal(statement.read(), from_db.lang_statements[lang].read())
        st = package.get_statement(lang)
        st_db = from_db.get_statement(lang)
        assert_contents_equal(st.read(), st_db.read())


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple", "run", "inwer"], indirect=True)
def test_tests_from_db(get_package):
    package_info: PackageInfo = get_package()
    package, _ = _save_and_test_simple(package_info)
    from_db: Sinolpack = sio3pack.from_db(1)

    tests = package.tests
    db_tests = from_db.tests

    assert len(tests) > 0
    assert len(tests) == len(db_tests)
    db_tests_dict = {}
    for test in db_tests:
        db_tests_dict[test.test_id] = test

    for test in tests:
        test_id = test.test_id
        assert test_id in db_tests_dict
        db_test = db_tests_dict[test_id]
        assert test.test_name == db_test.test_name
        assert test.group == db_test.group
        if test.in_file is None:
            assert db_test.in_file is None
        else:
            assert db_test.in_file is not None
            assert_contents_equal(test.in_file.read(), db_test.in_file.read())

        if test.out_file is None:
            assert db_test.out_file is None
        else:
            assert db_test.out_file is not None
            assert_contents_equal(test.out_file.read(), db_test.out_file.read())
