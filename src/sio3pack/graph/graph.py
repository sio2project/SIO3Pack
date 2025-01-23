from sio3pack.graph.node import Node


class Graph:
    """
    A class to represent a job graph.
    """
    start_node = Node("start")

    end_node = Node("end")

    unpack_node = Node("unpack")

    nodes = [start_node, unpack_node, end_node]

    _graph = {
        start_node: [unpack_node],
        unpack_node: [end_node],
        end_node: []
    }

    @classmethod
    def from_dict(cls, data: dict):
        return Graph(data["name"])

    def __init__(self, name: str):
        self.name = name

    def get_prog_files(self) -> list[str]:
        """
        Get all program files in the graph.
        """
        raise NotImplementedError()

