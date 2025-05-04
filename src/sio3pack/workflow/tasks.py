import re

from sio3pack.workflow import Object
from sio3pack.workflow.execution.channels import Channel
from sio3pack.workflow.execution.filesystems import Filesystem, FilesystemManager
from sio3pack.workflow.execution.mount_namespace import MountNamespace, MountNamespaceManager
from sio3pack.workflow.execution.process import Process
from sio3pack.workflow.execution.resource_group import ResourceGroup, ResourceGroupManager


class Task:
    """
    Base class for a task.
    """

    @classmethod
    def from_json(cls, data: dict, workflow: "Workflow"):
        """
        Create a new task from a dictionary.

        :param dict data: The dictionary to create the task from.
        :param Workflow workflow: The workflow the task belongs to.
        """
        if data["type"] == "execution":
            return ExecutionTask.from_json(data, workflow)
        elif data["type"] == "script":
            return ScriptTask.from_json(data, workflow)
        else:
            raise ValueError(f"Unknown task type: {data['type']}")

    def to_json(self, reg_map: dict[str, int] = None) -> dict:
        """
        Convert the task to a dictionary.

        :param reg_map: A mapping of register names to register numbers.
        :return dict: The dictionary representation of the task.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the task with the given replacements.

        :param replacements: The replacements to make.
        """
        raise NotImplementedError("Subclasses must implement this method.")


class ExecutionTask(Task):
    """
    A task that executes a program.

    :param name: The name of the task.
    :param Workflow workflow: The workflow the task belongs to.
    :param bool exclusive: Whether the task is exclusive.
    :param int hard_time_limit: The hard time limit.
    :param int extra_limit: If set, the hard_time_limit for the task will be the maximum time limit of all resource groups plus this value.
    :param int | str output_register: The output register of the task.
    :param int pid_namespaces: The number of PID namespaces.
    :param list[Process] processes: The processes of the task.
    :param int pipes: The number of pipes available to the task.
    :param list[Channel] channels: Configuration of the channels for the task.
    """

    def __init__(
        self,
        name: str,
        workflow: "Workflow",
        exclusive: bool = False,
        hard_time_limit: int = None,
        extra_limit: int = None,
        output_register: int | str = None,
        pid_namespaces: int = 1,
        processes: list[Process] = None,
        pipes: int = 0,
        channels: list[Channel] = None,
    ):
        """
        Create a new execution task.

        :param name: The name of the task.
        :param workflow: The workflow the task belongs to.
        :param exclusive: Whether the task is exclusive.
        :param hard_time_limit: The hard time limit.
        :param extra_limit: If set, the hard_time_limit for the task will be the maximum time limit of all resource groups
        plus this value.
        :param output_register: The output register of the task.
        :param pid_namespaces: The number of PID namespaces.
        :param processes: The processes of the task.
        :param pipes: The number of pipes.
        :param channels: Configuration of the channels for the task.
        """
        self.name = name
        self.workflow = workflow
        self.exclusive = exclusive
        if hard_time_limit is not None:
            self.hard_time_limit = hard_time_limit
        self.output_register = output_register
        self.pid_namespaces = pid_namespaces
        self.processes = processes or []
        self.pipes = pipes
        self.extra_limit = extra_limit
        self.channels = channels or []

        self.filesystem_manager = FilesystemManager(self)
        self.mountnamespace_manager = MountNamespaceManager(self, self.filesystem_manager)
        self.resource_group_manager = ResourceGroupManager(self)

    @classmethod
    def from_json(cls, data: dict, workflow: "Workflow"):
        """
        Create a new execution task from a dictionary.

        :param dict data: The dictionary to create the task from.
        :param Workflow workflow: The workflow the task belongs to.
        """
        channels = []
        for channel in data.get("channels", []):
            channels.append(Channel.from_json(channel))
        task = cls(
            data["name"],
            workflow,
            data["exclusive"],
            data.get("hard_time_limit"),
            output_register=data.get("output_register"),
            pid_namespaces=data["pid_namespaces"],
            pipes=int(data["pipes"]),
            channels=channels,
        )
        task.filesystem_manager.from_json(data["filesystems"], workflow)
        task.mountnamespace_manager.from_json(data["mount_namespaces"])
        task.resource_group_manager.from_json(data["resource_groups"])
        task.processes = [Process.from_json(process, workflow, task) for process in data["processes"]]
        return task

    def to_json(self, reg_map: dict[str, int] = None) -> dict:
        """
        Convert the task to a dictionary.

        :param reg_map: A mapping of register names to register numbers.
        :return dict: The dictionary representation of the task.
        """
        hard_time_limit = getattr(self, "hard_time_limit", 0)
        if self.extra_limit is not None:
            hard_time_limit = 0
            for rg in self.resource_group_manager.all():
                hard_time_limit = max(hard_time_limit, rg.time_limit)
            hard_time_limit += self.extra_limit

        if reg_map:
            self.output_register = reg_map.get(self.output_register, self.output_register)

        res = {
            "name": self.name,
            "type": "execution",
            "channels": [channel.to_json() for channel in self.channels],
            "exclusive": self.exclusive,
            "hard_time_limit": hard_time_limit,
            "output_register": self.output_register,
            "pid_namespaces": self.pid_namespaces,
            "filesystems": self.filesystem_manager.to_json(),
            "mount_namespaces": self.mountnamespace_manager.to_json(),
            "pipes": self.pipes,
            "resource_groups": self.resource_group_manager.to_json(),
            "processes": [process.to_json() for process in self.processes],
        }
        return res

    def add_filesystem(self, filesystem: Filesystem):
        """
        Add a filesystem to the task.

        :param Filesystem filesystem: The filesystem to add.
        """

        self.filesystem_manager.add(filesystem)

    def add_mount_namespace(self, mount_namespace: MountNamespace):
        """
        Add a mount namespace to the task.

        :param MountNamespace mount_namespace: The mount namespace to add.
        """
        self.mountnamespace_manager.add(mount_namespace)

    def add_resource_group(self, resource_group: ResourceGroup):
        """
        Add a resource group to the task.

        :param ResourceGroup resource_group: The resource group to add.
        """
        self.resource_group_manager.add(resource_group)

    def add_process(self, process: Process):
        """
        Add a process to the task.

        :param Process process: The process to add.
        """
        self.processes.append(process)

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the task with the given replacements.

        :param replacements: The replacements to make.
        """
        for process in self.processes:
            process.replace_templates(replacements)
        self.filesystem_manager.replace_templates(replacements)
        for key, value in replacements.items():
            if key in self.name:
                self.name = self.name.replace(key, value)
            if isinstance(self.output_register, str) and key in self.output_register:
                self.output_register = self.output_register.replace(key, value)


class ScriptTask(Task):
    """
    A task that runs a script.

    :param str name: The name of the task.
    :param Workflow workflow: The workflow the task belongs to.
    :param bool reactive: Whether the task is reactive.
    :param list[int | str] input_registers: The input registers of the task.
    :param list[int | str] output_registers: The output registers of the task.
    :param list[Object] objects: The objects the task uses.
    :param str script: The script to run.
    """

    def __init__(
        self,
        name: str,
        workflow: "Workflow",
        reactive: bool = False,
        input_registers: list[int | str] = None,
        output_registers: list[int | str] = None,
        objects: list[Object] = None,
        script: str = None,
    ):
        """
        Create a new script task.
        :param name: The name of the task.
        :param workflow: The workflow the task belongs to.
        :param reactive: Whether the task is reactive.
        :param input_registers: The input registers of the task.
        :param output_registers: The output registers of the task.
        :param objects: The objects the task uses.
        :param script: The script to run.
        """
        self.name = name
        self.workflow = workflow
        self.reactive = reactive
        self.input_registers = input_registers or []
        self.output_registers = output_registers or []
        self.objects = objects or []
        self.script = script

    def __str__(self):
        return f"<ScriptTask {self.name} reactive={self.reactive}>"

    @classmethod
    def from_json(cls, data: dict, workflow: "Workflow"):
        """
        Create a new script task from a dictionary.

        :param data: The dictionary to create the task from.
        :param workflow: The workflow the task belongs to.
        """
        return cls(
            data["name"],
            workflow,
            data["reactive"],
            data["input_registers"],
            data["output_registers"],
            [workflow.objects_manager.get_or_create_object(obj) for obj in data.get("objects", [])],
            data["script"],
        )

    def to_json(self, reg_map: dict[str, int] = None) -> dict:
        """
        Convert the task to a dictionary.

        :param reg_map: A mapping of register names to register numbers.
        :return: The dictionary representation of the task.
        """
        if reg_map:
            self.input_registers = [reg_map.get(reg, reg) for reg in self.input_registers]
            self.output_registers = [reg_map.get(reg, reg) for reg in self.output_registers]

            # Now, replace the register names in the script. Since we want this to not be slow
            # let's use regex.
            reg_pattern = r"<(r:[a-zA-Z0-9_]+)>"
            obs_pattern = r"<(obsreg:[a-zA-Z0-9_]+)>"
            self.script = re.sub(reg_pattern, lambda m: f"{reg_map.get(m.group(1), m.group(1))}", self.script)
            self.script = re.sub(obs_pattern, lambda m: f"{reg_map.get(m.group(1), m.group(1))}", self.script)

        res = {
            "name": self.name,
            "type": "script",
            "reactive": self.reactive,
            "input_registers": self.input_registers,
            "output_registers": self.output_registers,
            "script": self.script,
        }
        if self.objects:
            res["objects"] = [obj.handle for obj in self.objects]
        return res

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the task with the given replacements.

        :param replacements: The replacements to make.
        """
        for obj in self.objects:
            obj.replace_templates(replacements)
        for key, value in replacements.items():
            if key in self.name:
                self.name = self.name.replace(key, value)

            if key in self.script:
                self.script = self.script.replace(key, value)

            new_inputs = []
            for reg in self.input_registers:
                if isinstance(reg, str) and key in reg:
                    # If the replacement is a list, extend the new_inputs list with the values
                    if isinstance(value, list):
                        new_inputs.extend(value)
                    else:
                        new_inputs.append(reg.replace(key, value))
                else:
                    new_inputs.append(reg)
            self.input_registers = new_inputs

            new_outputs = []
            for reg in self.output_registers:
                if isinstance(reg, str) and key in reg:
                    # If the replacement is a list, extend the new_outputs list with the values
                    if isinstance(value, list):
                        new_outputs.extend(value)
                    else:
                        new_outputs.append(reg.replace(key, value))
                else:
                    new_outputs.append(reg)
            self.output_registers = new_outputs
