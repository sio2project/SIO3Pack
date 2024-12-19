from sio3pack.packages.exceptions import ImproperlyConfigured


class NoDjangoHandler:
    def __call__(self, *args, **kwargs):
        raise ImproperlyConfigured("sio3pack is not installed with Django support.")
