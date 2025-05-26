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


def pytest_ignore_collect(collection_path, config):
    if not __django_installed:
        return "test_django" in str(collection_path)


if __django_installed:

    @pytest.fixture(autouse=True)
    def clean_media_root(settings):
        """
        Clean the media root before each test.
        """
        import shutil
        import tempfile

        settings.MEDIA_ROOT = tempfile.mkdtemp()
        yield
        shutil.rmtree(settings.MEDIA_ROOT)
