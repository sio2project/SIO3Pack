class UnknownPackageType(Exception):
    def __init__(self, arg: str | int) -> None:
        if isinstance(arg, str):
            self.path = arg
            super().__init__(f"Unknown package type for file {arg}.")
        else:
            self.problem_id = arg
            super().__init__(f"Unknown package type for problem with id={arg}.")


class ImproperlyConfigured(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class PackageAlreadyExists(Exception):
    def __init__(self, problem_id: int) -> None:
        self.problem_id = problem_id
        super().__init__(f"A package already exists for problem with id={problem_id}.")
