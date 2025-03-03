from typing import Type

from django.core.files import File
from django.db import transaction

from sio3pack.django.common.models import SIO3Package, SIO3PackModelSolution, SIO3PackNameTranslation, SIO3PackStatement
from sio3pack.files.local_file import LocalFile
from sio3pack.files.remote_file import RemoteFile
from sio3pack.packages.exceptions import ImproperlyConfigured, PackageAlreadyExists


class DjangoHandler:
    def __init__(self, package: Type["Package"], problem_id: int):
        self.package = package
        self.problem_id = problem_id
        try:
            self.db_package = SIO3Package.objects.get(problem_id=self.problem_id)
        except SIO3Package.DoesNotExist:
            self.db_package = None

    @transaction.atomic
    def save_to_db(self):
        """
        Save the package to the database.
        """
        if SIO3Package.objects.filter(problem_id=self.problem_id).exists():
            raise PackageAlreadyExists(self.problem_id)

        self.db_package = SIO3Package.objects.create(
            problem_id=self.problem_id,
            short_name=self.package.short_name,
            full_name=self.package.full_name,
        )

        self._save_translated_titles()
        self._save_model_solutions()
        self._save_problem_statements()

    def _save_translated_titles(self):
        """
        Save the translated titles to the database.
        """
        for lang, title in self.package.lang_titles.items():
            SIO3PackNameTranslation.objects.create(
                package=self.db_package,
                language=lang,
                name=title,
            )

    def _save_model_solutions(self):
        for order, solution in enumerate(self.package.model_solutions):
            instance = SIO3PackModelSolution(
                package=self.db_package,
                name=solution.filename,
                order_key=order,
            )
            instance.source_file.save(solution.filename, File(open(solution.path, "rb")))

    def _save_problem_statements(self):
        def _add_statement(language: str, statement: LocalFile):
            instance = SIO3PackStatement(
                package=self.db_package,
                language=language,
            )
            instance.content.save(statement.filename, File(open(statement.path, "rb")))

        if self.package.get_statement():
            _add_statement("", self.package.get_statement())
        for lang, statement in self.package.lang_statements.items():
            _add_statement(lang, statement)

    @property
    def short_name(self) -> str:
        return self.db_package.short_name

    @property
    def full_name(self) -> str:
        return self.db_package.full_name

    @property
    def lang_titles(self) -> dict[str, str]:
        return {t.language: t.name for t in self.db_package.translated_titles.all()}

    @property
    def model_solutions(self) -> list[RemoteFile]:
        return [RemoteFile(s.source_file.path) for s in self.db_package.model_solutions.all()]

    @property
    def lang_statements(self) -> dict[str, RemoteFile]:
        return {s.language: RemoteFile(s.content.path) for s in self.db_package.statements.all()}
