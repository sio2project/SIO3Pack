from sio3pack.exceptions.general import SIO3PackException


class UnknownPackageType(SIO3PackException):
    def __init__(self, arg: str | int) -> None:
        if isinstance(arg, str):
            self.path = arg
            super().__init__(
                f"Unknown package type for file {arg}.",
                "Tried to load a package which is not a recognized package type. " f"The package is located at: {arg}",
            )
        else:
            self.problem_id = arg
            super().__init__(
                f"Unknown package type for problem with id={arg}.",
                "Tried to load a package from the database which does not exist or is not a recognized package type.",
            )


class ImproperlyConfigured(SIO3PackException):
    pass


class PackageAlreadyExists(SIO3PackException):
    def __init__(self, problem_id: int) -> None:
        self.problem_id = problem_id
        super().__init__(
            f"A package already exists for problem with id={problem_id}.",
            "Tried to create a package for a problem which already has a package. "
            "Please remove the existing package first or use a different problem ID.",
        )


class ProcessPackageError(SIO3PackException):
    pass
