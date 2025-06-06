from sio3pack.exceptions import ImproperlyConfigured


class NoDjangoHandler:
    def __call__(self, *args, **kwargs):
        raise ImproperlyConfigured(
            "sio3pack is not installed with Django support.",
            "from_db function was used, but sio3pack isn't installed with Django support. "
            "Read the documentation to learn more.",
        )
