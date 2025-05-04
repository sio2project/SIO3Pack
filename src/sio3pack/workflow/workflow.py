from sio3pack.workflow import ExecutionTask, Object, ScriptTask
from sio3pack.workflow.object import ObjectList, ObjectsManager
from sio3pack.workflow.tasks import Task


class Workflow:
    """
    A class to represent a job workflow. Number of registers is not required,
    as it is calculated automatically.

    :param str name: The name of the workflow.
    :param ObjectList external_objects: The external objects used in the workflow.
    :param ObjectList observable_objects: The observable objects used in the workflow.
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

        self.external_objects = ObjectList()
        for obj in external_objects or []:
            self.external_objects.append(self.objects_manager.get_or_create_object(obj))

        self.observable_objects = ObjectList()
        for obj in observable_objects or []:
            self.observable_objects.append(self.objects_manager.get_or_create_object(obj))

    def __str__(self):
        return f"<Workflow {self.name} tasks={[task for task in self.tasks]}>"

    def get_num_registers(self) -> int:
        """
        Get number of currently used registers.
        """
        if self.only_string_registers():
            num = 0
            for task in self.tasks:
                if isinstance(task, ExecutionTask) and task.output_register is not None:
                    num += 1
                if isinstance(task, ScriptTask):
                    num += len(task.input_registers) + len(task.output_registers)
            return num

        num_registers = 0
        for task in self.tasks:
            if isinstance(task, ExecutionTask):
                num_registers = max(num_registers, task.output_register)
            if isinstance(task, ScriptTask):
                num_registers = max([num_registers, max(task.input_registers), max(task.output_registers)])
        return num_registers + 1 if len(self.tasks) > 0 else 0

    def only_string_registers(self) -> bool:
        """
        Check if all registers in the workflow are strings.

        :return bool: True if all registers are strings, False otherwise.
        """
        for task in self.tasks:
            if isinstance(task, ExecutionTask):
                if not isinstance(task.output_register, str):
                    return False
            elif isinstance(task, ScriptTask):
                for reg in task.input_registers:
                    if not isinstance(reg, str):
                        return False
                for reg in task.output_registers:
                    if not isinstance(reg, str):
                        return False
        return True

    def to_json(self, to_int_regs: bool = False) -> dict:
        """
        Convert the workflow to a dictionary.

        :param bool to_int_regs: Whether to convert registers to integers.
        :return dict: The dictionary representation of the workflow.
        """
        if to_int_regs:
            if not self.only_string_registers():
                raise TypeError("Not all registers are strings")

            observable_regs = set()
            regs = set()
            for task in self.tasks:
                if isinstance(task, ExecutionTask):
                    if task.output_register.startswith("obsreg"):
                        observable_regs.add(task.output_register)
                    else:
                        regs.add(task.output_register)
                elif isinstance(task, ScriptTask):
                    for reg in task.input_registers:
                        if reg.startswith("obsreg"):
                            observable_regs.add(reg)
                        else:
                            regs.add(reg)
                    for reg in task.output_registers:
                        if reg.startswith("obsreg"):
                            observable_regs.add(reg)
                        else:
                            regs.add(reg)

            num_observable_regs = len(observable_regs)
            observable_regs = {name: i for i, name in enumerate(sorted(observable_regs))}
            regs = {name: i + len(observable_regs) for i, name in enumerate(sorted(regs))}
            reg_map = {**observable_regs, **regs}
            return {
                "name": self.name,
                "external_objects": [obj.handle for obj in self.external_objects],
                "observable_objects": [obj.handle for obj in self.observable_objects],
                "observable_registers": num_observable_regs,
                "tasks": [task.to_json(reg_map) for task in self.tasks],
                "registers": self.get_num_registers(),
            }

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

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the workflow with the given replacements.

        :param dict[str, str] replacements: The replacements to make.
        """
        for task in self.tasks:
            task.replace_templates(replacements)
        for obj in self.external_objects:
            obj.replace_templates(replacements)
        for obj in self.observable_objects:
            obj.replace_templates(replacements)

    def union(self, other: "Workflow"):
        """
        Add another workflow to this workflow. Merge all objects and tasks.

        :param Workflow other: Other workflow to merge into this.
        """
        # TODO: maybe add validating that two tasks dont create
        #   objects with the same name?

        # Merge objects.
        self.observable_objects.union(other.observable_objects)
        self.external_objects.union(other.external_objects)

        # Merge tasks.
        self.tasks += other.tasks

        # If registers are not strings, we need to increase `self.observable_registers`
        if not self.only_string_registers():
            self.observable_registers += other.observable_registers
