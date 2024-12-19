import os
import re
import tempfile
from typing import Any

import yaml

from sio3pack import LocalFile
from sio3pack.files import File
from sio3pack.graph import Graph, GraphManager, GraphOperation
from sio3pack.packages.exceptions import ImproperlyConfigured
from sio3pack.packages.package import Package
from sio3pack.packages.sinolpack.enums import ModelSolutionKind
from sio3pack.util import naturalsort_key
from sio3pack.utils.archive import Archive, UnrecognizedArchiveFormat


class Sinolpack(Package):
    """
    Represents a OIOIOI's standard problem package.
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
    def identify_from_db(cls, problem_id: int) -> bool:
        """
        Identifies whether problem is a Sinolpack.

        :param problem_id: ID of the problem.
        :return: True when problem is a Sinolpack, otherwise False.
        """
        from sio3pack.django.sinolpack.models import SinolpackPackage

        return SinolpackPackage.objects.filter(problem_id=problem_id).exists()

    def __del__(self):
        if hasattr(self, "tmpdir"):
            self.tmpdir.cleanup()

    def __init__(self):
        super().__init__()

    def _from_file(self, file: LocalFile, django_settings=None):
        super()._from_file(file)
        if self.is_archive:
            archive = Archive(file.path)
            self.short_name = self._find_main_dir(archive)
            self.tmpdir = tempfile.TemporaryDirectory()
            archive.extract(to_path=self.tmpdir.name)
            self.rootdir = os.path.join(self.tmpdir.name, self.short_name)
        else:
            # FIXME: Won't work in sinol-make.
            self.short_name = os.path.basename(file.path)
            self.rootdir = file.path

        try:
            graph_file = self.get_in_root("graph.json")
            self.graph_manager = GraphManager.from_file(graph_file)
        except FileNotFoundError:
            self.has_custom_graph = False

        self.django_settings = django_settings

        self._process_package()

    def _from_db(self, problem_id: int):
        super()._from_db(problem_id)
        super()._setup_django_handler(problem_id)
        if not self.django_enabled:
            raise ImproperlyConfigured("sio3pack is not installed with Django support.")

    def _default_graph_manager(self) -> GraphManager:
        return GraphManager(
            {
                "unpack": Graph.from_dict(
                    {
                        "name": "unpack",
                        # ...
                    }
                )
            }
        )

    def _get_from_django_settings(self, key: str, default=None):
        if self.django_settings is None:
            return default
        return getattr(self.django_settings, key, default)

    def get_doc_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's documents.
        """
        return os.path.join(self.rootdir, "doc")

    def get_in_doc_dir(self, filename: str) -> LocalFile:
        """
        Returns the path to the input file in the documents' directory.
        """
        return LocalFile(os.path.join(self.get_doc_dir(), filename))

    def get_in_root(self, filename: str) -> LocalFile:
        """
        Returns the path to the input file in the root directory.
        """
        return LocalFile(os.path.join(self.rootdir, filename))

    def get_prog_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's program files.
        """
        return os.path.join(self.rootdir, "prog")

    def get_in_prog_dir(self, filename: str) -> LocalFile:
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

        if not self.has_custom_graph:
            # Create the graph with processed files.
            # TODO: Uncomment this line when Graph will work.
            # self.graph_manager = self._default_graph_manager()
            pass

    def get_config(self) -> dict[str, Any]:
        """
        Returns the configuration of the problem.
        """
        return self.config

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

    def get_titles(self) -> dict[str, str]:
        """
        Returns a dictionary of problem titles, where keys are language codes and values are titles.
        """
        return self.lang_titles

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

    def _get_model_solutions(self) -> list[tuple[ModelSolutionKind, LocalFile]]:
        """
        Returns a list of model solutions, where each element is a tuple of model solution kind and filename.
        """
        if not os.path.exists(self.get_prog_dir()):
            return []

        regex = self.get_model_solution_regex()
        model_solutions = []
        for file in os.listdir(self.get_prog_dir()):
            match = re.match(regex, file)
            if match and os.path.isfile(os.path.join(self.get_prog_dir(), file)):
                file = LocalFile(os.path.join(self.get_prog_dir(), file))
                model_solutions.append((ModelSolutionKind.from_regex(match.group(1)), file))

        return model_solutions

    def sort_model_solutions(
        self, model_solutions: list[tuple[ModelSolutionKind, LocalFile]]
    ) -> list[tuple[ModelSolutionKind, LocalFile]]:
        """
        Sorts model solutions by kind.
        """

        def sort_key(model_solution):
            kind, file = model_solution
            return kind.value, naturalsort_key(file.filename[: file.filename.index(".")])

        return list(sorted(model_solutions, key=sort_key))

    def get_model_solutions(self) -> list[tuple[ModelSolutionKind, LocalFile]]:
        """
        Returns a list of model solutions, where each element is a tuple of model solution kind and filename.
        """
        return self.model_solutions

    def get_additional_files(self) -> list[LocalFile]:
        """
        Returns a list of additional files.
        """
        return self.additional_files

    def _process_prog_files(self):
        """
        Process all files in the problem's program directory that are used.
        Saves all models solution files. If the problem has a custom graph file,
        takes the files that are used in the graph. Otherwise, ingen, inwer and
        files in `extra_compilation_files` and `extra_execution_files` from config
        are saved.
        """

        # Process model solutions.
        self.model_solutions = self.sort_model_solutions(self._get_model_solutions())

        if self.has_custom_graph:
            self.additional_files = self.graph_manager.get_prog_files()
        else:
            self.additional_files = []
            self.additional_files.extend(self.config.get("extra_compilation_files", []))
            self.additional_files.extend(self.config.get("extra_execution_files", []))
            extensions = self.get_submittable_extensions()
            self.special_files: dict[str, bool] = {}
            for file in ("ingen", "inwer", "soc", "chk"):
                try:
                    self.additional_files.append(
                        LocalFile.get_file_matching_extension(self.get_prog_dir(), self.short_name + file, extensions)
                    )
                    self.special_files[file] = True
                except FileNotFoundError:
                    self.special_files[file] = False

    def get_statements(self) -> dict[str, File]:
        """
        Returns a dictionary of problem statements, where keys are language codes and values are files.
        """
        return self.lang_statements

    def get_statement(self, lang: str | None = None) -> File:
        """
        Returns the problem statement for a given language code.
        """
        if lang is None:
            return self.statement
        return self.lang_statements.get(lang, None)

    def _process_statements(self):
        """
        Creates a problem statement from html or pdf source.

        TODO: we have to support this somehow, but we can't use makefiles. Probably a job for sio3workers.
        If `USE_SINOLPACK_MAKEFILES` is set to True in the OIOIOI settings,
        the pdf file will be compiled from a LaTeX source.
        """
        self.statement = None
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
                #     self.short_name + lang + '.html.zip', File(open(htmlzipfile, 'rb'))
                # )
            except FileNotFoundError:
                pass

            try:
                pdffile = self.get_in_doc_dir(f"{self.short_name}zad{lang}.pdf")
                if lang == "":
                    self.statement = pdffile
                else:
                    self.lang_statements[lang[1:]] = pdffile
            except FileNotFoundError:
                pass

    def get_attachments(self) -> list[LocalFile]:
        """
        Returns a list of attachments.
        """
        return self.attachments

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

    def get_unpack_graph(self) -> GraphOperation | None:
        try:
            return GraphOperation(
                self.graph_manager.get("unpack"),
                True,
                self._unpack_return_data,
            )
        except KeyError:
            return None

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
