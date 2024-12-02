from typing import Type

from sio3pack.packages.exceptions import ImproperlyConfigured


class DjangoHandler:
    def __init__(self, package: Type["Package"], problem_id: int):
        self.package = package
        self.problem_id = problem_id


class NoDjangoHandler:
    def __call__(self, *args, **kwargs):
        raise ImproperlyConfigured("sio3pack is not installed with Django support.")
