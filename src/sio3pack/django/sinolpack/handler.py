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
from sio3pack.files.remote_file import RemoteFile
from sio3pack.packages.sinolpack.enums import ModelSolutionKind


class SinolpackDjangoHandler(DjangoHandler):

    def __init__(self, package: Type["Package"], problem_id: int):
        super().__init__(package, problem_id)
        self.db_package = None

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
        return self.db_package.config.parsed_config

    @property
    def model_solutions(self) -> list[tuple[ModelSolutionKind, RemoteFile]]:
        solutions = SinolpackModelSolution.objects.filter(package=self.db_package)
        return [(s.kind, RemoteFile(s.source_file.path)) for s in solutions]

    @property
    def additional_files(self) -> list[RemoteFile]:
        return [RemoteFile(f.file.path) for f in self.db_package.additional_files.all()]

    @property
    def attachments(self) -> list[RemoteFile]:
        return [RemoteFile(f.content.path) for f in self.db_package.attachments.all()]
