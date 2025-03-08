import json

from sio3pack.files import File
from sio3pack.workflow.workflow import Workflow


class WorkflowManager:
    @classmethod
    def from_file(cls, file: File):
        graphs = {}
        content = json.loads(file.read())
        for name, graph in content.items():
            graphs[name] = Workflow.from_dict(graph)
        return cls(graphs)

    def __init__(self, graphs: dict[str, Workflow]):
        self.graphs = graphs

    def get_prog_files(self) -> list[str]:
        """
        Get all program files used in all graphs.
        """
        files = set()
        for graph in self.graphs.values():
            files.update(graph.get_prog_files())
        return list(files)

    def get(self, name: str) -> Workflow:
        return self.graphs[name]
