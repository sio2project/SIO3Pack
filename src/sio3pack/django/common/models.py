import os

from django.conf import settings
from django.db import models
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _

try:
    from oioioi.filetracker.fields import FileField
except ImportError:
    FileField = models.FileField


def make_problem_filename(instance, filename):
    if not isinstance(instance, SIO3Package):
        try:
            instance = instance.package
        except AttributeError:
            raise ValueError(
                f"make_problem_filename used on an object {type(instance)} which does not have " f"a package attribute"
            )
    return f"sio3pack/{instance.problem_id}/{get_valid_filename(filename)}"


class SIO3Package(models.Model):
    """
    A generic package type.
    """

    problem_id = models.IntegerField()
    short_name = models.CharField(max_length=30, verbose_name=_("short name"))
    full_name = models.CharField(max_length=255, default="", verbose_name=_("full name"))

    def __str__(self):
        return f"<SIO3Package {self.short_name}>"


class SIO3PackNameTranslation(models.Model):
    """
    Model to store translated task's title.
    """

    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE)
    language = models.CharField(max_length=7, choices=settings.LANGUAGES, verbose_name=_("language code"))
    name = models.CharField(max_length=255, verbose_name=_("name translation"))

    def __str__(self):
        return f"<SIO3PackNameTranslation for {self.package.short_name} in {self.language}>"

    class Meta:
        verbose_name = _("sio3pack's name translation")
        verbose_name_plural = _("sio3pack's name translations")
        unique_together = ("package", "language")


class SIO3PackModelSolution(models.Model):
    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name=_("name"))
    source_file = FileField(upload_to=make_problem_filename, verbose_name=_("source file"))
    order_key = models.IntegerField(default=0)

    def __str__(self):
        return f"<SIO3PackModelSolution {self.short_name}>"

    @property
    def short_name(self):
        return self.name.rsplit(".", 1)[0]


class SIO3PackStatement(models.Model):
    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE)
    language = models.CharField(
        max_length=7, blank=True, null=True, choices=settings.LANGUAGES, verbose_name=_("language code")
    )
    content = FileField(upload_to=make_problem_filename, verbose_name=_("content"))

    @property
    def filename(self):
        return os.path.split(self.content.name)[1]

    @property
    def download_name(self):
        return self.package.short_name + self.extension

    @property
    def extension(self):
        return os.path.splitext(self.content.name)[1].lower()

    def __str__(self):
        return f"<SIO3PackStatement {self.package.short_name} in {self.language}>"

    class Meta(object):
        verbose_name = _("problem statement")
        verbose_name_plural = _("problem statements")
