import json
import os
import re
import tempfile
from typing import Any, Type

import yaml

from sio3pack.files import File, LocalFile
from sio3pack.packages.exceptions import ImproperlyConfigured
from sio3pack.packages.package import Package
from sio3pack.packages.package.configuration import SIO3PackConfig
from sio3pack.packages.sinolpack import constants
from sio3pack.packages.sinolpack.enums import ModelSolutionKind
from sio3pack.packages.sinolpack.workflows import SinolpackWorkflowManager
from sio3pack.test import Test
from sio3pack.util import naturalsort_key
from sio3pack.utils.archive import Archive, UnrecognizedArchiveFormat
from sio3pack.workflow import Workflow, WorkflowManager, WorkflowOperation


class Sinolpack(Package):
    """
    Represents a OIOIOI's standard problem package.

    :param str short_name: Short name of the problem.
    :param str full_name: Full name of the problem.
    :param dict[str, str] lang_titles: A dictionary of problem titles,
        where keys are language codes and values are titles.
    :param dict[str, File] lang_statements: A dictionary of problem
        statements, where keys are language codes and values are files.
    :param dict[str, Any] config: Configuration of the problem.
    :param list[dict[str, Any]] model_solutions: A list
        of model solutions, where each element is a dict containing
        a model solution kind and a file.
    :param list[File] additional_files: A list of additional files for
        the problem.
    :param list[File] attachments: A list of attachments related to the problem.
    :param WorkflowManager workflow_manager: A workflow manager for the problem.
    :param File | None main_model_solution: The main model solution file.
    :param dict[str, File | None] special_files: A dictionary of special files,
        where keys are file names and values are booleans indicating
        whether the file exists or not.
    :param list[Test] tests: A list of tests, where each element is a
        :class:`sio3pack.Test` object.
    :param bool is_from_db: A flag indicating whether the package
        is loaded from the database or not.
    :param SinolpackWorkflowManager workflow_manager: A workflow manager for the problem.
    """

    django_handler = "sio3pack.django.sinolpack.handler.SinolpackDjangoHandler"

    @classmethod
    def _find_main_dir(cls, archive: Archive) -> str | None:
        dirs = list(map(os.path.normcase, archive.dirnames()))
        dirs = list(map(os.path.normpath, dirs))
        toplevel_dirs = list(set(f.split(os.sep)[0] for f in dirs))
        problem_dirs = []
        for dir in toplevel_dirs:
            for required_subdir in ("in", "out"):
                if all(f.split(os.sep)[:2] != [dir, required_subdir] for f in dirs):
                    break
            else:
                problem_dirs.append(dir)
        if len(problem_dirs) == 1:
            return problem_dirs[0]

        return None

    @classmethod
    def identify(cls, file: LocalFile) -> bool:
        """
        Identifies whether file is a Sinolpack.

        :param file: File with package.
        :return: True when file is a Sinolpack, otherwise False.
        """
        path = file.path
        try:
            archive = Archive(path)
            return cls._find_main_dir(archive) is not None
        except UnrecognizedArchiveFormat:
            return os.path.exists(os.path.join(path, "in")) and os.path.exists(os.path.join(path, "out"))

    @classmethod
    def identify_db(cls, problem_id: int) -> bool:
        """
        Identifies whether problem is a Sinolpack.

        :param problem_id: ID of the problem.
        :return: True when problem is a Sinolpack, otherwise False.
        """
        from sio3pack.django.common.models import SIO3Package

        return SIO3Package.objects.filter(problem_id=problem_id).exists()

    def __del__(self):
        if hasattr(self, "tmpdir"):
            self.tmpdir.cleanup()

    def __init__(self):
        super().__init__()

    def _from_file(self, file: LocalFile, configuration: SIO3PackConfig = None):
        super()._from_file(file, configuration)
        if self.is_archive:
            archive = Archive(file.path)
            self.short_name = self._find_main_dir(archive)
            self.tmpdir = tempfile.TemporaryDirectory()
            archive.extract(to_path=self.tmpdir.name)
            self.rootdir = os.path.join(self.tmpdir.name, self.short_name)
        else:
            # FIXME: Won't work in sinol-make.
            self.short_name = os.path.basename(os.path.abspath(file.path))
            self.rootdir = os.path.abspath(file.path)

        if os.path.exists(os.path.join(self.rootdir, "workflows.json")):
            try:
                with open(os.path.join(self.rootdir, "workflows.json"), "r") as f:
                    workflows = json.load(f)
                self.workflow_manager = SinolpackWorkflowManager(self, workflows)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in workflows.json: {e}")
        else:
            self.workflow_manager = self._default_workflow_manager()

        self._process_package()

    def _from_db(self, problem_id: int, configuration: SIO3PackConfig = None):
        super()._from_db(problem_id, configuration)
        super()._setup_django_handler(problem_id)
        # TODO: Workflows probably should be fetched only if they are needed, since this can be slow
        super()._setup_workflows_from_db()
        if not self.django_enabled:
            raise ImproperlyConfigured("sio3pack is not installed with Django support.")

    def _workflow_manager_class(self) -> Type[WorkflowManager]:
        return SinolpackWorkflowManager

    def get_doc_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's documents.
        """
        return os.path.join(self.rootdir, "doc")

    def get_in_doc_dir(self, filename: str) -> File:
        """
        Returns the path to the input file in the documents' directory.
        """
        return LocalFile(os.path.join(self.get_doc_dir(), filename))

    def get_in_root(self, filename: str) -> File:
        """
        Returns the path to the input file in the root directory.
        """
        return LocalFile(os.path.join(self.rootdir, filename))

    def get_prog_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's program files.
        """
        return os.path.join(self.rootdir, "prog")

    def get_in_prog_dir(self, filename: str) -> File:
        """
        Returns the path to the input file in the program directory.
        """
        return LocalFile(os.path.join(self.get_prog_dir(), filename))

    def get_attachments_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's attachments.
        """
        return os.path.join(self.rootdir, "attachments")

    def _process_package(self):
        self._process_config_yml()
        self._detect_full_name()
        self._detect_full_name_translations()
        self._process_prog_files()
        self._process_statements()
        self._process_attachments()
        self._process_existing_tests()

    def _process_config_yml(self):
        """
        Process the config.yml file. If it exists, it will be loaded into the config attribute.
        """
        try:
            config = self.get_in_root("config.yml")
            self.config = yaml.safe_load(config.read())
        except FileNotFoundError:
            self.config = {}

    def _detect_full_name(self):
        """
        Sets the problem's full name from the ``config.yml`` (key ``title``)
        or from the ``title`` tag in the LaTeX source file (backwards compatibility).
        The ``config.yml`` file takes precedence over the LaTeX source.

        Example of how the ``title`` tag may look like:
        \title{A problem}
        """
        if "title" in self.config:
            self.full_name = self.config["title"]
            return

        try:
            source = self.get_in_doc_dir(self.short_name + "zad.tex")
            text = source.read()
            r = re.search(r"^[^%]*\\title{(.+)}", text, re.MULTILINE)
            if r is not None:
                self.full_name = r.group(1)
        except FileNotFoundError:
            pass

    def get_title(self, lang: str | None = None) -> str:
        """
        Returns the problem title for a given language code.
        """
        if lang is None:
            return self.full_name
        return self.lang_titles.get(lang, self.full_name)

    def _detect_full_name_translations(self):
        """Creates problem's full name translations from the ``config.yml``
        (keys matching the pattern ``title_[a-z]{2}``, where ``[a-z]{2}`` represents
        two-letter language code defined in ``settings.py``), if any such key is given.
        """
        self.lang_titles = {}
        for lang_code, _ in self._get_from_django_settings("LANGUAGES", [("en", "English")]):
            key = f"title_{lang_code}"
            if key in self.config:
                self.lang_titles[lang_code] = self.config[key]

    def get_submittable_extensions(self):
        """
        Returns a list of extensions that are submittable.
        """
        return self.config.get(
            "submittable_langs",
            self._get_from_django_settings("SUBMITTABLE_LANGUAGES", ["c", "cpp", "cc", "cxx", "py"]),
        )

    def get_model_solution_regex(self):
        """
        Returns the regex used to determine model solutions.
        """
        extensions = self.get_submittable_extensions()
        return rf"^{self.short_name}[0-9]*([bs]?)[0-9]*(_.*)?\.({'|'.join(extensions)})"

    def main_model_solution_regex(self):
        """
        Returns the regex used to determine main model solution.
        """
        extensions = self.get_submittable_extensions()
        return rf"^{self.short_name}\.({'|'.join(extensions)})"

    def _get_model_solutions(self) -> list[dict[str, Any]]:
        """
        Returns a list of model solutions, where each element is a dict of model solution kind and filename.
        """
        if not os.path.exists(self.get_prog_dir()):
            return []

        regex = self.get_model_solution_regex()
        model_solutions = []
        main_solution: File | None = None
        main_regex = self.main_model_solution_regex()
        for file in os.listdir(self.get_prog_dir()):
            match = re.match(regex, file)
            if match and os.path.isfile(os.path.join(self.get_prog_dir(), file)):
                file = LocalFile(os.path.join(self.get_prog_dir(), file))
                model_solutions.append({"file": file, "kind": ModelSolutionKind.from_regex(match.group(1))})
                if re.match(main_regex, file.filename):
                    main_solution = file

        self.main_model_solution = main_solution
        return model_solutions

    def sort_model_solutions(self, model_solutions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Sorts model solutions by kind.
        """

        def sort_key(model_solution):
            kind: ModelSolutionKind = model_solution["kind"]
            file: LocalFile = model_solution["file"]
            return kind.value, naturalsort_key(file.filename[: file.filename.index(".")])

        return list(sorted(model_solutions, key=sort_key))

    def special_file_types(self) -> list[str]:
        """
        Returns the list of special file types.
        """
        return ["ingen", "inwer", "soc", "chk"]

    def _process_prog_files(self):
        """
        Process all files in the problem's program directory that are used.
        Saves all models solution files. If the problem has a custom workflow file,
        takes the files that are used in the workflow. Otherwise, ingen, inwer and
        files in `extra_compilation_files` and `extra_execution_files` from config
        are saved.
        """

        # Process model solutions.
        self.model_solutions = self.sort_model_solutions(self._get_model_solutions())

        self.additional_files = []
        self.additional_files.extend(self.config.get("extra_compilation_files", []))
        self.additional_files.extend(self.config.get("extra_execution_files", []))
        extensions = self.get_submittable_extensions()
        self.special_files: dict[str, File | None] = {}
        for file in self.special_file_types():
            try:
                lf = LocalFile.get_file_matching_extension(self.get_prog_dir(), self.short_name + file, extensions)
                self.additional_files.append(lf)
                self.special_files[file] = lf
            except FileNotFoundError:
                self.special_files[file] = None

    def get_statement(self, lang: str | None = None) -> File | None:
        """
        Returns the problem statement for a given language code.
        """
        return self.lang_statements.get(lang or "", None)

    def _process_statements(self):
        """
        Creates a problem statement from html or pdf source.

        TODO: we have to support this somehow, but we can't use makefiles. Probably a job for sio3workers.
        If `USE_SINOLPACK_MAKEFILES` is set to True in the OIOIOI settings,
        the pdf file will be compiled from a LaTeX source.
        """
        self.lang_statements = {}
        docdir = self.get_doc_dir()
        if not os.path.exists(docdir):
            return

        lang_prefs = [""] + [
            f"-{lang}" for lang, _ in self._get_from_django_settings("LANGUAGES", [("en", "English"), ("pl", "Polish")])
        ]

        for lang in lang_prefs:
            try:
                htmlzipfile = self.get_in_doc_dir(f"{self.short_name}zad{lang}.html.zip")
                # TODO: what to do with html?
                # if self._html_disallowed():
                #     raise ProblemPackageError(
                #         _(
                #             "You cannot upload package with "
                #             "problem statement in HTML. "
                #             "Try again using PDF format."
                #         )
                #     )
                #
                # self._force_index_encoding(htmlzipfile)
                # statement = ProblemStatement(problem=self.problem, language=lang[1:])
                # statement.content.save(
                #     self.short_name + lang + '.html.zip', LocalFile(open(htmlzipfile, 'rb'))
                # )
            except FileNotFoundError:
                pass

            try:
                pdffile = self.get_in_doc_dir(f"{self.short_name}zad{lang}.pdf")
                if lang == "":
                    self.lang_statements[""] = pdffile
                else:
                    self.lang_statements[lang[1:]] = pdffile
            except FileNotFoundError:
                pass

    def _process_attachments(self):
        """ """
        attachments_dir = self.get_attachments_dir()
        if not os.path.isdir(attachments_dir):
            self.attachments = []
            return
        self.attachments = [
            LocalFile(os.path.join(attachments_dir, attachment))
            for attachment in os.listdir(attachments_dir)
            if os.path.isfile(os.path.join(attachments_dir, attachment))
        ]

    def _get_test_regex(self) -> str:
        return rf"^{self.short_name}(([0-9]+)([a-z]?[a-z0-9]*)).(in|out)$"

    def match_test_regex(self, filename: str) -> re.Match | None:
        """
        Returns match object if the filename matches the test regex.
        """
        return re.match(self._get_test_regex(), filename)

    def get_test_id_from_filename(self, filename: str) -> str:
        """
        Returns the test ID from the filename.
        """
        match = self.match_test_regex(filename)
        if match:
            return match.group(1)
        raise ValueError(f"Invalid filename format: {filename}")

    def get_group_from_filename(self, filename: str) -> str:
        """
        Returns the group from the filename.
        """
        match = self.match_test_regex(filename)
        if match:
            return match.group(2)
        raise ValueError(f"Invalid filename format: {filename}")

    def _process_existing_tests(self):
        """
        Process pre-existing input and output tests.
        """
        # TODO: Rewrite this
        test_ids = set()
        for ext in ("in", "out"):
            for file in os.listdir(os.path.join(self.rootdir, ext)):
                match = self.match_test_regex(os.path.basename(file))
                if match:
                    test_name = os.path.splitext(os.path.basename(file))[0]
                    test_id = match.group(1)
                    group = match.group(2)
                    test_ids.add((test_id, group, test_name))
        # TODO: Sort this properly
        test_ids = sorted(test_ids)
        self.tests = []

        for test_id, group, test_name in test_ids:
            if os.path.exists(os.path.join(self.rootdir, "in", self.short_name + test_id + ".in")):
                in_file = LocalFile(os.path.join(self.rootdir, "in", self.short_name + test_id + ".in"))
            else:
                in_file = None
            if os.path.exists(os.path.join(self.rootdir, "out", self.short_name + test_id + ".out")):
                out_file = LocalFile(os.path.join(self.rootdir, "out", self.short_name + test_id + ".out"))
            else:
                out_file = None
            self.tests.append(Test(test_name, test_id, in_file, out_file, group))

    def get_input_tests(self) -> list[Test]:
        """
        Returns the list of tests with input files.
        """
        return [test for test in self.tests if test.in_file is not None]

    def get_test(self, test_id: str) -> Test:
        """
        Returns the test with the given ID.
        """
        for test in self.tests:
            if test.test_id == test_id:
                return test
        raise ValueError(f"Test with ID {test_id} not found.")

    def get_tests_with_inputs(self) -> list[Test]:
        """
        Returns the list of input tests.
        """
        return [test for test in self.tests if test.in_file is not None]

    def get_corresponding_out_filename(self, in_test: str) -> str:
        """
        Returns the corresponding output test for the given input test.
        """
        # TODO: Better
        return in_test.replace(".in", ".out")

    def get_outgen_path(self) -> str | None:
        return self.main_model_solution.path

    def _get_special_file_path(self, file_type: str) -> str | None:
        """
        Returns the path to the special file in the program directory.
        """
        # TODO: This should be faster
        if self.special_files[file_type]:
            return self.special_files[file_type].path
        return None

    def get_inwer_path(self) -> str | None:
        return self._get_special_file_path("inwer")

    def get_checker_file(self) -> File | None:
        """
        Returns the checker file.
        """
        return self.special_files["chk"]

    def get_checker_path(self) -> str | None:
        return self._get_special_file_path("chk")

    def get_unpack_operation(self, return_func: callable = None) -> WorkflowOperation | None:
        has_ingen = self.special_files["ingen"] is not None
        has_outgen = self.main_model_solution is not None
        has_inwer = self.special_files["inwer"] is not None
        return self.workflow_manager.get_unpack_operation(has_ingen, has_outgen, has_inwer, return_func)

    def _unpack_return_data(self, data: dict):
        """
        Adds data received from the unpack operation to the package.
        """
        # TODO: implement. The unpack will probably return tests, so we need to process them.
        pass

    def save_to_db(self, problem_id: int):
        """
        Save the package to the database. If sio3pack isn't installed with Django
        support, it should raise an ImproperlyConfigured exception.
        """
        self._setup_django_handler(problem_id)
        if not self.django_enabled:
            raise ImproperlyConfigured("sio3pack is not installed with Django support.")
        self.django.save_to_db()

    def _get_compiler_flags(self, lang: str) -> list[str]:
        """
        Extends the compiler flags with the ones from the config.yml file.
        """

        flags = super()._get_compiler_flags(lang)
        if "extra_compilation_args" in self.config and lang in self.config["extra_compilation_args"]:
            config_flags = self.config["extra_compilation_args"][lang]
            if isinstance(config_flags, str):
                config_flags = [config_flags]
            flags.extend(config_flags)
        return flags

    def get_extra_execution_files(self) -> list[File]:
        """
        Returns the list of extra execution files specified in the config.yml file.
        If no such files are specified, an empty list is returned.

        :return: List of extra execution files.
        """
        if self.is_from_db:
            return self.django.extra_execution_files
        else:
            return [
                LocalFile(os.path.join(self.rootdir, "prog", f))
                for f in self.config.get("extra_execution_files", [])
                if os.path.isfile(os.path.join(self.rootdir, f))
            ]

    def get_extra_compilation_files(self) -> list[File]:
        """
        Returns the list of extra compilation files specified in the config.yml file.
        If no such files are specified, an empty list is returned.

        :return: List of extra compilation files.
        """
        if self.is_from_db:
            return self.django.extra_compilation_files
        else:
            return [
                LocalFile(os.path.join(self.rootdir, "prog", f))
                for f in self.config.get("extra_compilation_files", [])
                if os.path.isfile(os.path.join(self.rootdir, f))
            ]

    def _get_limit(self, test: Test, language: str, type: str) -> int:
        """
        Helper function to get a time/memory limit for a test from the config.

        :param test: The test to get the limit for.
        :param language: The language of the program.
        :param type: The type of limit to get (time or memory).
        :return: The limit for the test in seconds or bytes.
        """
        if type not in ("time", "memory"):
            raise ValueError("Type must be either 'time' or 'memory'")

        def get(conf) -> int:
            if f"{type}_limits" in conf:
                if test.test_id in conf[f"{type}_limits"]:
                    return conf[f"{type}_limits"][test.test_id]
                if test.group in conf[f"{type}_limits"]:
                    return conf[f"{type}_limits"][test.group]
            if f"{type}_limit" in conf:
                return conf[f"{type}_limit"]
            return None

        if "override_limits" in self.config and language in self.config["override_limits"]:
            limit = get(self.config["override_limits"][language])
            if limit is not None:
                return limit
        limit = get(self.config)
        if limit is not None:
            return limit
        if type == "memory":
            return constants.DEFAULT_MEMORY_LIMIT
        else:
            return constants.DEFAULT_TIME_LIMIT

    def get_time_limit_for_test(self, test: Test, language: str) -> int:
        """
        Returns the time limit for the given test.
        Read the Sinolpack specification for more details.

        :param test: The test to get the time limit for.
        :param language: The language of the program.
        :return: The time limit for the test in seconds.
        """
        return self._get_limit(test, language, "time")

    def get_memory_limit_for_test(self, test: Test, language: str) -> int:
        """
        Returns the memory limit for the given test.
        Read the Sinolpack specification for more details.

        :param test: The test to get the memory limit for.
        :param language: The language of the program.
        :return: The memory limit for the test in bytes.
        """
        return self._get_limit(test, language, "memory")
