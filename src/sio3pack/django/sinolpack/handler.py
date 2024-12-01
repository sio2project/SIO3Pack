from sio3pack.django.sinolpack.models import SinolpackPackage
from sio3pack.packages.exceptions import PackageAlreadyExists
from sio3pack.packages.package.django.handler import DjangoHandler


class SinolpackDjangoHandler(DjangoHandler):

    def save_to_db(self):
        """
        Save the package to the database.
        """
        if SinolpackPackage.objects.filter(problem_id=self.problem_id).exists():
            raise PackageAlreadyExists(self.problem_id)

        SinolpackPackage.objects.create(
            problem_id=self.problem_id,
            short_name=self.package.short_name,
        )
