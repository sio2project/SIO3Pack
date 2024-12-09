import os

import yaml
from django.conf import settings
from django.db import models
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _

from sio3pack.packages.sinolpack.enums import ModelSolutionKind

try:
    from oioioi.filetracker.fields import FileField
except ImportError:
    FileField = models.FileField


def make_problem_filename(instance, filename):
    if not isinstance(instance, SinolpackPackage):
        try:
            instance = instance.package
        except AttributeError:
            raise ValueError(
                f"make_problem_filename used on an object {type(instance)} which does not have " f"a package attribute"
            )
    return f"sio3pack/sinolpack/{instance.problem_id}/{get_valid_filename(filename)}"


class SinolpackPackage(models.Model):
    """
    A package for the sinolpack package type.
    """

    problem_id = models.IntegerField()
    short_name = models.CharField(max_length=30, verbose_name=_("short name"))
    full_name = models.CharField(max_length=255, default="", verbose_name=_("full name"))

    def __str__(self):
        return f"<SinolpackPackage {self.short_name}>"


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

    def __str__(self):
        return f"<SinolpackConfig for {self.package.short_name}>"

    class Meta:
        verbose_name = _("sinolpack's configuration")
        verbose_name_plural = _("sinolpack's configurations")


class SinolpackNameTranslation(models.Model):
    """
    Model to store translations of sinolpack package names.
    """

    package = models.ForeignKey(SinolpackPackage, on_delete=models.CASCADE)
    language = models.CharField(max_length=7, choices=settings.LANGUAGES, verbose_name=_("language code"))
    name = models.CharField(max_length=255, verbose_name=_("name translation"))

    def __str__(self):
        return f"<SinolpackNameTranslation for {self.package.short_name} in {self.language}>"

    class Meta:
        verbose_name = _("sinolpack's name translation")
        verbose_name_plural = _("sinolpack's name translations")
        unique_together = ("package", "language")


class SinolpackModelSolution(models.Model):
    package = models.ForeignKey(SinolpackPackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, verbose_name=_("name"))
    source_file = FileField(upload_to=make_problem_filename, verbose_name=_("source file"))
    kind_name = models.CharField(max_length=1, choices=ModelSolutionKind.django_choices(), verbose_name=_("kind"))
    order_key = models.IntegerField(default=0)

    def __str__(self):
        return f"<SinolpackModelSolution {self.short_name}>"

    @property
    def short_name(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def kind(self):
        return ModelSolutionKind(self.kind_name)


class SinolpackAdditionalFile(models.Model):
    package = models.ForeignKey(SinolpackPackage, on_delete=models.CASCADE)
    name = models.CharField(max_length=30, verbose_name=_("name"))
    file = FileField(upload_to=make_problem_filename, verbose_name=_("file"))

    def __str__(self):
        return f"<SinolpackAdditionalFile {self.name}>"

    class Meta:
        verbose_name = _("additional file")
        verbose_name_plural = _("additional files")


class SinolpackProblemStatement(models.Model):
    package = models.ForeignKey(SinolpackPackage, on_delete=models.CASCADE)
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
        return f"<SinolpackProblemStatement {self.package.short_name} in {self.language}>"

    class Meta(object):
        verbose_name = _("problem statement")
        verbose_name_plural = _("problem statements")


class SinolpackAttachment(models.Model):
    package = models.ForeignKey(SinolpackPackage, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, verbose_name=_("description"))
    content = FileField(upload_to=make_problem_filename, verbose_name=_("file"))

    @property
    def filename(self):
        return os.path.split(self.content.name)[1]

    def __str__(self):
        return f"<SinolpackAttachment {self.filename}>"

    class Meta(object):
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")
