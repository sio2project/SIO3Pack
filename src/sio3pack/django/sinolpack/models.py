import os

import yaml
from django.db import models
from django.utils.translation import gettext_lazy as _

from sio3pack.django.common.models import SIO3Package, SIO3PackModelSolution, make_problem_filename
from sio3pack.packages.sinolpack.enums import ModelSolutionKind

try:
    from oioioi.filetracker.fields import FileField
except ImportError:
    FileField = models.FileField


class SinolpackConfig(models.Model):
    """
    Model to store ``config.yml`` present in Sinolpack packages.
    """

    package = models.OneToOneField(SIO3Package, on_delete=models.CASCADE, related_name="config")
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


class SinolpackModelSolution(SIO3PackModelSolution):
    kind_name = models.CharField(max_length=1, choices=ModelSolutionKind.django_choices(), verbose_name=_("kind"))

    def __str__(self):
        return f"<SinolpackModelSolution {self.short_name}>"

    @property
    def short_name(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def kind(self):
        return ModelSolutionKind(self.kind_name)


class SinolpackAdditionalFile(models.Model):
    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE, related_name="additional_files")
    name = models.CharField(max_length=30, verbose_name=_("name"))
    file = FileField(upload_to=make_problem_filename, verbose_name=_("file"))

    def __str__(self):
        return f"<SinolpackAdditionalFile {self.name}>"

    class Meta:
        verbose_name = _("additional file")
        verbose_name_plural = _("additional files")


class SinolpackSpecialFile(models.Model):
    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE, related_name="special_files")
    type = models.CharField(max_length=30, verbose_name=_("type"))
    additional_file = models.OneToOneField(
        SinolpackAdditionalFile, on_delete=models.CASCADE, related_name="special_file"
    )

    def __str__(self):
        return f"<SinolpackSpecialFile {self.type} {self.additional_file}>"

    class Meta:
        verbose_name = _("special file")
        verbose_name_plural = _("special files")


class SinolpackAttachment(models.Model):
    package = models.ForeignKey(SIO3Package, on_delete=models.CASCADE, related_name="attachments")
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
