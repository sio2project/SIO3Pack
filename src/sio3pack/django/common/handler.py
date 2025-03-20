from typing import Any, Type

from django.core.files import File
from django.db import transaction

import sio3pack
from sio3pack.django.common.models import SIO3Package, SIO3PackModelSolution, SIO3PackNameTranslation, SIO3PackStatement
from sio3pack.files import LocalFile, RemoteFile
from sio3pack.packages.exceptions import ImproperlyConfigured, PackageAlreadyExists


class DjangoHandler:
    """
    Base class for handling Django models.
    Allows to save the package to the database and retrieve its data.

    :param sio3pack.Package package: The package to handle.
    :param int problem_id: The problem ID.
    """

    def __init__(self, package: "sio3pack.Package", problem_id: int):
        """
        Initialize the handler with the package and problem ID.
        :param sio3pack.Package package: The package to handle.
        :param int problem_id: The problem ID.
        """
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
        """
        Short name of the problem.
        """
        return self.db_package.short_name

    @property
    def full_name(self) -> str:
        """
        Full name of the problem.
        """
        return self.db_package.full_name

    @property
    def lang_titles(self) -> dict[str, str]:
        """
        A dictionary of problem titles,
        where keys are language codes and values are titles.
        """
        return {t.language: t.name for t in self.db_package.name_translations.all()}

    @property
    def model_solutions(self) -> list[dict[str, Any]]:
        """
        A list of model solutions, where each element is a dictionary containing
        a :class:`sio3pack.RemoteFile` object.
        """
        return [{"file": RemoteFile(s.source_file.path)} for s in self.db_package.model_solutions.all()]

    @property
    def lang_statements(self) -> dict[str, RemoteFile]:
        """
        A dictionary of problem statements, where keys are language codes and values are files.
        """
        return {s.language: RemoteFile(s.content.path) for s in self.db_package.statements.all()}
