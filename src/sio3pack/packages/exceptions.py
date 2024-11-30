class UnknownPackageType(Exception):
    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(f"Unknown package type for file {path}.")
