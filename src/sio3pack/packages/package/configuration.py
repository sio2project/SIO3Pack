class CompilerConfig:
    def __init__(self, name: str, full_name: str, path: str, flags: list[str]):
        self.name = name
        self.full_name = full_name
        self.path = path
        self.flags = flags


class SIO3PackConfig:
    """
    Configuration class for SIO3Pack.
    """

    def __init__(self, django_settings=None, compilers_config: dict[str, CompilerConfig] = None, extensions_config: dict[str, str] = None):
        """
        Initialize the configuration with Django settings.

        :param django_settings: Django settings object.
        :param compilers_config: Dictionary of compiler configurations. The keys are the compiler names,
            and the values are CompilerConfig objects.
        :param extensions_config: Dictionary of language configurations. The keys are the file extensions,
            and the values are the corresponding languages.
        """
        self.django_settings = django_settings
        self.compilers_config = compilers_config if compilers_config else {}
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
