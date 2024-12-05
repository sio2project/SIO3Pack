from sio3pack.django.sinolpack.models import SinolpackPackage
from django.utils.text import get_valid_filename


def make_problem_filename(instance, filename):
    if not isinstance(instance, SinolpackPackage):
        try:
            instance = instance.package
        except AttributeError:
            raise ValueError(f'make_problem_filename used on an object {type(instance)} which does not have '
                             f'a package attribute')
    return f'sio3pack/sinolpack/{instance.problem_id}/{get_valid_filename(filename)}'
