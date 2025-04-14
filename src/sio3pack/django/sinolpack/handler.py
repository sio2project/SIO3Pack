from typing import Any, Type

import yaml
from django.core.files import File
from django.db import transaction

from sio3pack.django.common.handler import DjangoHandler
from sio3pack.django.sinolpack.models import (
    SinolpackAdditionalFile,
    SinolpackAttachment,
    SinolpackConfig,
    SinolpackModelSolution,
)
from sio3pack.files import RemoteFile
from sio3pack.packages.sinolpack.enums import ModelSolutionKind


class SinolpackDjangoHandler(DjangoHandler):
    """
    Handler for Sinolpack packages in Django.
    Has additional properties like config, model_solutions, additional_files and attachments.
    """

    def __init__(self, package: "sio3pack.Sinolpack", problem_id: int):
        super().__init__(package, problem_id)

    @transaction.atomic
    def save_to_db(self):
        """
        Save the package to the database.
        """
        super(SinolpackDjangoHandler, self).save_to_db()

        self._save_config()
        self._save_additional_files()
        self._save_attachments()

    def _save_config(self):
        """
        Save the ``config.yml`` to the database.
        """
        config = self.package.config
        SinolpackConfig.objects.create(
            package=self.db_package,
            config=yaml.dump(config),
        )

    def _save_model_solutions(self):
        for order, (kind, solution) in enumerate(self.package.model_solutions):
            instance = SinolpackModelSolution(
                package=self.db_package,
                name=solution.filename,
                kind_name=kind.value,
                order_key=order,
            )
            instance.source_file.save(solution.filename, File(open(solution.path, "rb")))

    def _save_additional_files(self):
        for file in self.package.additional_files:
            instance = SinolpackAdditionalFile(
                package=self.db_package,
                name=file.filename,
            )
            instance.file.save(file.filename, File(open(file.path, "rb")))

    def _save_attachments(self):
        for attachment in self.package.attachments:
            instance = SinolpackAttachment(
                package=self.db_package,
                description=attachment.filename,
            )
            instance.content.save(attachment.filename, File(open(attachment.path, "rb")))

    @property
    def config(self) -> dict[str, Any]:
        """
        Config file of the package.
        """
        return self.db_package.config.parsed_config

    @property
    def model_solutions(self) -> list[dict[str, Any]]:
        """
        A list of model solutions, where each element is a dictionary containing a :class:`sio3pack.RemoteFile` object
        and the :class:`sio3pack.packages.sinolpack.enums.ModelSolutionKind` kind.
        """
        solutions = SinolpackModelSolution.objects.filter(package=self.db_package)
        return [{"file": RemoteFile(s.source_file.path), "kind": s.kind} for s in solutions]

    @property
    def additional_files(self) -> list[RemoteFile]:
        """
        A list of additional files (as :class:`sio3pack.RemoteFile`) for the problem.
        """
        return [RemoteFile(f.file.path) for f in self.db_package.additional_files.all()]

    @property
    def attachments(self) -> list[RemoteFile]:
        """
        A list of attachments (as :class:`sio3pack.RemoteFile`) related to the problem.
        """
        return [RemoteFile(f.content.path) for f in self.db_package.attachments.all()]
