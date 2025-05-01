from sio3pack.workflow import Object, ExecutionTask, ScriptTask
from sio3pack.workflow.object import ObjectsManager
from sio3pack.workflow.tasks import Task


class Workflow:
    """
    A class to represent a job workflow. Number of registers is not required,
    as it is calculated automatically.

    :param str name: The name of the workflow.
    :param list[Object] external_objects: The external objects used in the workflow.
    :param list[Object] observable_objects: The observable objects used in the workflow.
    :param int observable_registers: The number of observable registers used in the workflow.
    :param list[Task] tasks: The tasks in the workflow.
    """

    @classmethod
    def from_json(cls, data: dict):
        """
        Create a new workflow from a dictionary.

        :param data: The dictionary to create the workflow from.
        """
        workflow = cls(data["name"], data["external_objects"], data["observable_objects"], data["observable_registers"])
        for task in data["tasks"]:
            workflow.add_task(Task.from_json(task, workflow))
        return workflow

    def __init__(
        self,
        name: str,
        external_objects: list[str] = None,
        observable_objects: list[str] = None,
        observable_registers: int = 0,
        tasks: list[Task] = None,
    ):
        """
        Create a new workflow. Number of required registers is calculated automatically.

        :param str name: The name of the workflow.
        :param list[str] external_objects: The external objects used in the workflow.
        :param list[str] observable_objects: The observable objects used in the workflow.
        :param int observable_registers: The number of observable registers used in the workflow.
        :param list[Task] tasks: The tasks in the workflow.
        """
        self.name = name
        self.observable_registers = observable_registers
        self.tasks = tasks or []
        self.objects_manager = ObjectsManager()

        self.external_objects = []
        for obj in external_objects or []:
            self.external_objects.append(self.objects_manager.get_or_create_object(obj))

        self.observable_objects = []
        for obj in observable_objects or []:
            self.observable_objects.append(self.objects_manager.get_or_create_object(obj))

    def __str__(self):
        return f"<Workflow {self.name} tasks={[task for task in self.tasks]}>"

    def get_num_registers(self) -> int:
        """
        Get number of currently used registers.
        """
        num_registers = 0
        for task in self.tasks:
            if isinstance(task, ExecutionTask):
                num_registers = max(num_registers, task.output_register)
            if isinstance(task, ScriptTask):
                num_registers = max([num_registers, max(task.input_registers), max(task.output_registers)])
        return num_registers + 1 if len(self.tasks) > 0 else 0

    def to_json(self) -> dict:
        """
        Convert the workflow to a dictionary.

        :return dict: The dictionary representation of the workflow.
        """
        return {
            "name": self.name,
            "external_objects": [obj.handle for obj in self.external_objects],
            "observable_objects": [obj.handle for obj in self.observable_objects],
            "registers": self.get_num_registers(),
            "observable_registers": self.observable_registers,
            "tasks": [task.to_json() for task in self.tasks],
        }

    def add_task(self, task: Task):
        """
        Add a task to the workflow.

        :param Task task: The task to add.
        """
        self.tasks.append(task)

    def get_prog_files(self) -> list[str]:
        """
        Get all program files in the workflow.

        :return: A list of program files.
        """
        raise NotImplementedError()

    def add_external_object(self, obj: Object):
        """
        Add an external object to the workflow.

        :param Object obj: The object to add.
        """
        self.external_objects.append(obj)

    def add_observable_object(self, obj: Object):
        """
        Add an observable object to the workflow.

        :param Object obj: The object to add.
        """
        self.observable_objects.append(obj)

    def union(self, other: "Workflow"):
        """
        Add another workflow to this workflow. Merges external /
        observable objects and recalculates registers so there
        are no confilicts.

        :param Workflow other: Other workflow to merge into this.
        """
        # TODO: maybe add validating that two tasks dont create
        #   objects with the same name?

        # Merge objects.
        self.observable_objects = list(set(self.observable_objects + other.observable_objects))
        self.external_objects = list(set(self.external_objects + other.external_objects))

        # First, move registers in `self` workflow if `other workflow
        # has any observable registers, since they have to be in the beginning.
        to_move = other.observable_registers
        for task in self.tasks:
            if isinstance(task, ExecutionTask):
                if task.output_register >= self.observable_registers:
                    # This is non-observable register
                    task.output_register += to_move
            elif isinstance(task, ScriptTask):
                for i in range(len(task.output_registers)):
                    reg = task.output_registers[i]
                    if reg >= self.observable_registers:
                        # This is non-observable register
                        task.output_registers[i] += to_move
        self.observable_registers += to_move
