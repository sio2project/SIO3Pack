from typing import Type

import yaml
from django.core.files import File
from django.db import transaction

from sio3pack import LocalFile
from sio3pack.django.sinolpack.models import (SinolpackAdditionalFile,
                                              SinolpackAttachment,
                                              SinolpackConfig,
                                              SinolpackModelSolution,
                                              SinolpackNameTranslation,
                                              SinolpackPackage,
                                              SinolpackProblemStatement,)
from sio3pack.packages.exceptions import PackageAlreadyExists
from sio3pack.packages.package.django.handler import DjangoHandler


class SinolpackDjangoHandler(DjangoHandler):

    def __init__(self, package: Type["Package"], problem_id: int):
        super().__init__(package, problem_id)
        self.db_package = None

    @transaction.atomic
    def save_to_db(self):
        """
        Save the package to the database.
        """
        if SinolpackPackage.objects.filter(problem_id=self.problem_id).exists():
            raise PackageAlreadyExists(self.problem_id)

        self.db_package = SinolpackPackage.objects.create(
            problem_id=self.problem_id,
            short_name=self.package.short_name,
            full_name=self.package.full_name,
        )

        self._save_config()
        self._save_translated_titles()
        self._save_model_solutions()
        self._save_additional_files()
        self._save_problem_statements()
        self._save_attachments()

    def _save_config(self):
        """
        Save the ``config.yml`` to the database.
        """
        config = self.package.get_config()
        SinolpackConfig.objects.create(
            package=self.db_package,
            config=yaml.dump(config),
        )

    def _save_translated_titles(self):
        """
        Save the translated titles to the database.
        """
        for lang, title in self.package.get_titles().items():
            SinolpackNameTranslation.objects.create(
                package=self.db_package,
                language=lang,
                name=title,
            )

    def _save_model_solutions(self):
        for order, (kind, solution) in enumerate(self.package.get_model_solutions()):
            instance = SinolpackModelSolution(
                package=self.db_package,
                name=solution.filename,
                kind_name=kind.value,
                order_key=order,
            )
            instance.source_file.save(solution.filename, File(open(solution.path, "rb")))

    def _save_additional_files(self):
        for file in self.package.get_additional_files():
            instance = SinolpackAdditionalFile(
                package=self.db_package,
                name=file.filename,
            )
            instance.file.save(file.filename, File(open(file.path, "rb")))

    def _save_problem_statements(self):
        def _add_statement(language: str, statement: LocalFile):
            instance = SinolpackProblemStatement(
                package=self.db_package,
                language=language,
            )
            instance.content.save(statement.filename, File(open(statement.path, "rb")))

        if self.package.get_statement():
            _add_statement("", self.package.get_statement())
        for lang, statement in self.package.get_statements().items():
            _add_statement(lang, statement)

    def _save_attachments(self):
        for attachment in self.package.get_attachments():
            instance = SinolpackAttachment(
                package=self.db_package,
                description=attachment.filename,
            )
            instance.content.save(attachment.filename, File(open(attachment.path, "rb")))
