import pytest


try:
    import django
    __django_installed = True
except ImportError:
    __django_installed = False


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "no_django" in item.keywords:
            if __django_installed:
                item.add_marker(pytest.mark.skip(reason="Django is installed, skipping no_django tests."))


def pytest_ignore_collect(path, config):
    if not __django_installed:
        return "test_django" in str(path)
