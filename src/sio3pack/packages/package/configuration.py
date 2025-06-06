class CompilerConfig:
    """
    Configuration class for a compiler. It holds the name, full name, path, and flags of the compiler.

    :param name: The name of the compiler.
    :param full_name: The full name of the compiler, including version.
    :param path: The path to the compiler executable.
    :param flags: The flags to use when compiling with this compiler.
    """

    def __init__(self, name: str, full_name: str, path: str, flags: list[str]):
        self.name = name
        self.full_name = full_name
        self.path = path
        self.flags = flags

    @classmethod
    def detect(cls) -> dict[str, "CompilerConfig"]:
        """
        Detect the installed compilers and return them as the configuration.
        """
        # TODO: implement this properly
        return {
            "cpp": cls("g++", "g++-12.2", "g++", ["-std=c++20", "-O3"]),
            "python": cls("python", "python3.10", "python", []),
        }


class SIO3PackConfig:
    """
    Configuration class for SIO3Pack. It holds the configuration for compilers and file extensions.
    It can be initialized with Django settings or detected automatically.

    :param django_settings: Django settings object.
    :param compilers_config: Dictionary of compiler configurations. The keys are the compiler names,
        and the values are CompilerConfig objects.
    :param extensions_config: Dictionary of language configurations. The keys are the file extensions,
        and the values are the corresponding languages.
    """

    def __init__(
        self,
        django_settings=None,
        compilers_config: dict[str, CompilerConfig] = None,
        extensions_config: dict[str, str] = None,
        allow_unrecognized_files: bool = False,
    ):
        """
        Initialize the configuration with Django settings.

        :param django_settings: Django settings object.
        :param compilers_config: Dictionary of compiler configurations. The keys are the compiler names,
            and the values are CompilerConfig objects.
        :param extensions_config: Dictionary of language configurations. The keys are the file extensions,
            and the values are the corresponding languages.
        :param allow_unrecognized_files: If True, allows unrecognized files in in/ and out/ directories.
            This is useful when working with packages locally.
        """
        self.django_settings = django_settings
        self.compilers_config = compilers_config if compilers_config else {}
        self.allow_unrecognized_files = allow_unrecognized_files
        if extensions_config is None:
            self.extensions_config = {
                ".cpp": "cpp",
                ".cxx": "cpp",
                ".h": "cpp",
                ".hpp": "cpp",
                ".py": "python",
            }
        else:
            self.extensions_config = extensions_config

    @classmethod
    def detect(cls) -> "SIO3PackConfig":
        """
        Detect the installed compilers and return them as the configuration.
        """
        compilers_config = CompilerConfig.detect()
        extensions_config = {
            ".cpp": "cpp",
            ".cxx": "cpp",
            ".h": "cpp",
            ".hpp": "cpp",
            ".py": "python",
        }
        return cls(compilers_config=compilers_config, extensions_config=extensions_config)
