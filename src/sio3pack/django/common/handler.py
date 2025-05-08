import json
from typing import Any

from django.core.files import File
from django.db import transaction

import sio3pack
from sio3pack.django.common.models import (
    SIO3Package,
    SIO3PackMainModelSolution,
    SIO3PackModelSolution,
    SIO3PackNameTranslation,
    SIO3PackStatement,
    SIO3PackTest,
    SIO3PackWorkflow,
)
from sio3pack.files import LocalFile
from sio3pack.files.remote_file import RemoteFile
from sio3pack.packages.exceptions import PackageAlreadyExists
from sio3pack.test import Test
from sio3pack.workflow import Workflow


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
        self._save_main_model_solution()
        self._save_problem_statements()
        self._save_tests()

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

    def _save_main_model_solution(self):
        """
        Save the main model solution to the database.
        """
        instance = SIO3PackMainModelSolution(
            package=self.db_package,
        )
        instance.source_file.save(
            self.package.main_model_solution.filename, File(open(self.package.main_model_solution.path, "rb"))
        )
        instance.save()

    def _save_model_solutions(self):
        for order, solution in enumerate(self.package.model_solutions):
            instance = SIO3PackModelSolution(
                package=self.db_package,
                name=solution.filename,
                order_key=order,
            )
            instance.source_file.save(solution.filename, File(open(solution.path, "rb")))
            instance.save()

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

    def _save_tests(self):
        for test in self.package.tests:
            instance = SIO3PackTest(
                package=self.db_package,
                name=test.test_name,
                test_id=test.test_id,
                group=test.group,
            )
            if test.in_file:
                instance.input_file.save(test.in_file.filename, File(open(test.in_file.path, "rb")))
            if test.out_file:
                instance.output_file.save(test.out_file.filename, File(open(test.out_file.path, "rb")))
            instance.save()

    def _save_workflows(self):
        for name, wf in self.package.workflow_manager.all().items():
            instance = SIO3PackWorkflow(
                package=self.db_package,
                name=name,
                workflow_raw=json.dumps(wf.to_json()),
            )

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
        return [{"file": RemoteFile(s.source_file)} for s in self.db_package.model_solutions.all()]

    @property
    def main_model_solution(self) -> RemoteFile:
        """
        The main model solution as a :class:`sio3pack.RemoteFile`.
        """
        return RemoteFile(self.db_package.main_model_solution.source_file)

    @property
    def lang_statements(self) -> dict[str, RemoteFile]:
        """
        A dictionary of problem statements, where keys are language codes and values are files.
        """
        return {s.language: RemoteFile(s.content) for s in self.db_package.statements.all()}

    @property
    def tests(self) -> list[Test]:
        """
        A list of tests, where each element is a dictionary containing
        """
        return [
            Test(
                test_id=t.test_id,
                test_name=t.name,
                group=t.group,
                in_file=RemoteFile(t.input_file) if t.input_file else None,
                out_file=RemoteFile(t.output_file) if t.output_file else None,
            )
            for t in self.db_package.tests.all()
        ]

    @property
    def workflows(self) -> dict[str, Workflow]:
        """
        A dictionary of workflows, where keys are workflow names and values are :class:`sio3pack.Workflow` objects.
        """
        return {w.name: w.workflow for w in self.db_package.workflows.all()}
