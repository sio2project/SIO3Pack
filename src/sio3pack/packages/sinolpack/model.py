import os
import re
import tempfile

import yaml

from sio3pack.files.file import File
from sio3pack.graph.graph import Graph
from sio3pack.graph.graph_manager import GraphManager
from sio3pack.graph.graph_op import GraphOperation
from sio3pack.packages.package import Package
from sio3pack.packages.sinolpack.enums import ModelSolutionKind
from sio3pack.util import naturalsort_key
from sio3pack.utils.archive import Archive, UnrecognizedArchiveFormat


class Sinolpack(Package):
    """
    Represents a OIOIOI's standard problem package.
    """

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
    def identify(cls, file: File) -> bool:
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

    def __del__(self):
        if hasattr(self, "tmpdir"):
            self.tmpdir.cleanup()

    def __init__(self, file: File, django_settings=None):
        super().__init__(file)
        if self.is_archive:
            archive = Archive(file.path)
            self.short_name = self._find_main_dir(archive)
            self.tmpdir = tempfile.TemporaryDirectory()
            archive.extract(to_path=self.tmpdir.name)
            self.rootdir = os.path.join(self.tmpdir.name, self.short_name)
        else:
            self.short_name = os.path.basename(file.path)
            self.rootdir = file.path

        try:
            graph_file = self.get_in_root("graph.json")
            self.graph_manager = GraphManager.from_file(graph_file)
        except FileNotFoundError:
            self.has_custom_graph = False

        self.django_settings = django_settings

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

    def get_in_doc_dir(self, filename: str) -> File:
        """
        Returns the path to the input file in the documents' directory.
        """
        return File(os.path.join(self.get_doc_dir(), filename))

    def get_in_root(self, filename: str) -> File:
        """
        Returns the path to the input file in the root directory.
        """
        return File(os.path.join(self.rootdir, filename))

    def get_prog_dir(self) -> str:
        """
        Returns the path to the directory containing the problem's program files.
        """
        return os.path.join(self.rootdir, "prog")

    def get_in_prog_dir(self, filename: str) -> File:
        """
        Returns the path to the input file in the program directory.
        """
        return File(os.path.join(self.get_prog_dir(), filename))

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
            self.graph_manager = self._default_graph_manager()

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

    def _detect_full_name_translations(self):
        """Creates problem's full name translations from the ``config.yml``
        (keys matching the pattern ``title_[a-z]{2}``, where ``[a-z]{2}`` represents
        two-letter language code defined in ``settings.py``), if any such key is given.
        """
        self.lang_titles = {}
        for lang_code, lang in self._get_from_django_settings("LANGUAGES", [("en", "English")]):
            key = "title_%s" % lang_code
            if key in self.config:
                self.lang_titles[lang_code] = self.config[key]

    def get_submittable_extensions(self):
        """
        Returns a list of extensions that are submittable.
        """
        return self.config.get(
            "submittable_langs", self._get_from_django_settings("SUBMITTABLE_LANGUAGES", ["c", "cpp", "cxx", "py"])
        )

    def get_model_solution_regex(self):
        """
        Returns the regex used to determine model solutions.
        """
        extensions = self.get_submittable_extensions()
        return rf"^{self.short_name}[0-9]*([bs]?)[0-9]*(_.*)?\.(" + "|".join(extensions) + ")"

    def _get_model_solutions(self) -> list[tuple[ModelSolutionKind, str]]:
        """
        Returns a list of model solutions, where each element is a tuple of model solution kind and filename.
        """
        regex = self.get_model_solution_regex()
        model_solutions = []
        for file in os.listdir(self.get_prog_dir()):
            match = re.match(regex, file)
            if re.match(regex, file) and os.path.isfile(os.path.join(self.get_prog_dir(), file)):
                model_solutions.append((ModelSolutionKind.from_regex(match.group(1)), file))

        return model_solutions

    def sort_model_solutions(
        self, model_solutions: list[tuple[ModelSolutionKind, str]]
    ) -> list[tuple[ModelSolutionKind, str]]:
        """
        Sorts model solutions by kind.
        """

        def sort_key(model_solution):
            kind, name = model_solution
            return kind.value, naturalsort_key(name[: name.index(".")])

        return list(sorted(model_solutions, key=sort_key))

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
                        File.get_file_matching_extension(
                            self.get_prog_dir(), self.short_name + file, extensions
                        ).filename
                    )
                    self.special_files[file] = True
                except FileNotFoundError:
                    self.special_files[file] = False

    def _process_statements(self):
        """
        Creates a problem statement from html or pdf source.

        TODO: we have to support this somehow, but we can't use makefiles. Probably a job for sio3workers.
        If `USE_SINOLPACK_MAKEFILES` is set to True in the OIOIOI settings,
        the pdf file will be compiled from a LaTeX source.
        """
        docdir = self.get_doc_dir()
        if not os.path.exists(docdir):
            return

        lang_prefs = [""] + [
            "-" + l[0] for l in self._get_from_django_settings("LANGUAGES", [("en", "English"), ("pl", "Polish")])
        ]

        self.lang_statements = {}
        for lang in lang_prefs:
            try:
                htmlzipfile = self.get_in_doc_dir(self.short_name + "zad" + lang + ".html.zip")
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
                pdffile = self.get_in_doc_dir(self.short_name + "zad" + lang + ".pdf")
                if lang == "":
                    self.statement = pdffile
                else:
                    self.lang_statements[lang[1:]] = pdffile
            except:
                pass

    def _process_attachments(self):
        """ """
        attachments_dir = self.get_attachments_dir()
        if not os.path.isdir(attachments_dir):
            return
        self.attachments = [
            attachment
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
