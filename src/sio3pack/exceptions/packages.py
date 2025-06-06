from sio3pack.exceptions.general import SIO3PackException


class UnknownPackageType(SIO3PackException):
    """
    Exception raised when trying to load a package of an unknown type.
    This can happen when the package file is not recognized or when the package
    is not a valid package type in the database.

    :param str | int arg: The path to the package file or the problem ID.
    """

    def __init__(self, arg: str | int) -> None:
        """
        Initialize the UnknownPackageType exception.

        :param str | int arg: The path to the package file or the problem ID.
        """
        if isinstance(arg, str):
            self.path = arg
            super().__init__(
                f"Unknown package type for file {arg}.",
                "Tried to load a package which is not a recognized package type. Read the documentation "
                "to learn how to create a package and which are supported.",
            )
        else:
            self.problem_id = arg
            super().__init__(
                f"Unknown package type for problem with id={arg}.",
                "Tried to load a package from the database which does not exist or is not a recognized package type.",
            )


class ImproperlyConfigured(SIO3PackException):
    """
    Exception raised when the package is improperly configured, i.e., using Django features
    without Django being installed.
    """

    pass


class PackageAlreadyExists(SIO3PackException):
    """
    Exception raised when trying to create a package for a problem that already has a package.

    :param int problem_id: The ID of the problem for which the package already exists.
    """

    def __init__(self, problem_id: int) -> None:
        """
        Initialize the PackageAlreadyExists exception.

        :param int problem_id: The ID of the problem for which the package already exists.
        """

        self.problem_id = problem_id
        super().__init__(
            f"A package already exists for problem with id={problem_id}.",
            "Tried to create a package for a problem which already has a package. "
            "Please remove the existing package first or use a different problem ID.",
        )


class ProcessPackageError(SIO3PackException):
    """
    Exception raised when there is an error processing a package.
    """

    pass
