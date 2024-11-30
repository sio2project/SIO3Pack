class Graph:
    """
    A class to represent a job graph.
    """

    @classmethod
    def from_dict(cls, data: dict):
        raise NotImplementedError()

    def __init__(self, name: str):
        self.name = name

    def get_prog_files(self) -> list[str]:
        """
        Get all program files in the graph.
        """
        raise NotImplementedError()
