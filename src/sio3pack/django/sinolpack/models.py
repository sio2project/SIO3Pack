import yaml
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from sio3pack.django.sinolpack.utils import make_problem_filename
from sio3pack.packages.sinolpack.enums import ModelSolutionKind

try:
    from oioioi.filetracker.fields import FileField
except ImportError:
    FileField = models.FileField


class SinolpackPackage(models.Model):
    """
    A package for the sinolpack package type.
    """

    problem_id = models.IntegerField()
    short_name = models.CharField(max_length=30, verbose_name=_("short name"))
    full_name = models.CharField(max_length=255, verbose_name=_("full name"))


class SinolpackConfig(models.Model):
    """
    Model to store ``config.yml`` present in Sinolpack packages.
    """

    package = models.OneToOneField(SinolpackPackage, on_delete=models.CASCADE)
    config = models.TextField(verbose_name=_("config"))

    @property
    def parsed_config(self):
        if not self.config:
            return {}
        return yaml.safe_load(self.config)

    class Meta:
        verbose_name = _("sinolpack's configuration")
        verbose_name_plural = _("sinolpack's configurations")


class SinolpackNameTranslation(models.Model):
    """
    Model to store translations of sinolpack package names.
    """

    package = models.OneToOneField(SinolpackPackage, on_delete=models.CASCADE)
    language = models.CharField(max_length=2, choices=settings.LANGUAGES, verbose_name=_("language code"))
    name = models.CharField(max_length=255, verbose_name=_("name translation"))

    class Meta:
        verbose_name = _("sinolpack's name translation")
        verbose_name_plural = _("sinolpack's name translations")
        unique_together = ("package", "language")


class SinolpackModelSolution(models.Model):
    package = models.OneToOneField(SinolpackPackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, verbose_name=_("name"))
    source_file = FileField(upload_to=make_problem_filename, verbose_name=_("source file"))
    kind = models.CharField(max_length=1, choices=ModelSolutionKind.all(), verbose_name=_("kind"))
    order_key = models.IntegerField(default=0)

    @property
    def short_name(self):
        return self.name.rsplit('.', 1)[0]
