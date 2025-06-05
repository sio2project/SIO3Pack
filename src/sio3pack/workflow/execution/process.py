from sio3pack.exceptions import ParsingFailedOn, WorkflowParsingError
from sio3pack.workflow.execution.descriptors import DescriptorManager
from sio3pack.workflow.execution.mount_namespace import MountNamespace
from sio3pack.workflow.execution.resource_group import ResourceGroup


class Process:
    """
    A class to represent a process in a workflow.

    :param Workflow workflow: The workflow the process belongs to.
    :param Executiontask task: The task which the process belongs to.
    :param list[str] arguments: Executable arguments for the process.
    :param dict[str, str] environment: Environment variables for the process.
    :param str image: The image of the process, which can be a Docker image or similar.
    :param MountNamespace mount_namespace: The mount namespace to use for the process.
    :param ResourceGroup resource_group: The resource group of the process.
    :param str working_directory: The working directory of the process.
    :param int pid_namespace: The PID namespace of the process.
    :param list[int] start_after: The processes that must be finished before this process starts.
    """

    def __init__(
        self,
        workflow: "Workflow",
        task: "ExecutionTask",
        arguments: list[str] = None,
        environment: dict = None,
        image: str = "",
        mount_namespace: MountNamespace = None,
        resource_group: ResourceGroup = None,
        pid_namespace: int = 0,
        working_directory: str = "/",
        start_after: list[int] = None,
    ):
        """
        Represent a process.

        :param arguments: The arguments of the process.
        :param environment: The environment of the process.
        :param image: The image of the process.
        :param mount_namespace: The mount namespace of the process.
        :param resource_group: The resource group of the process.
        :param working_directory: The working directory of the process.
        :param pid_namespace: The PID namespace of the process.
        :param task: The task of the process.
        :param workflow: The workflow of the process.
        :param start_after: The processes that must be finished before this process starts.
        """
        self.arguments = arguments or []
        self.environment = environment or {}
        self.image = image
        self.mount_namespace = mount_namespace
        self.resource_group = resource_group
        self.pid_namespace = pid_namespace
        self.working_directory = working_directory
        self.task = task
        self.workflow = workflow
        self.descriptor_manager = DescriptorManager(workflow.objects_manager, task.filesystem_manager)
        self.start_after = start_after or []

    def to_json(self) -> dict:
        """
        Convert the process to a JSON-serializable dictionary.
        """

        return {
            "arguments": self.arguments,
            "environment": [f"{key}={value}" for key, value in self.environment.items()],
            "image": self.image,
            "mount_namespace": self.mount_namespace.id,
            "resource_group": self.resource_group.id,
            "pid_namespace": self.pid_namespace,
            "working_directory": self.working_directory,
            "descriptors": self.descriptor_manager.to_json(),
            "start_after": self.start_after,
        }

    @classmethod
    def from_json(cls, data: dict, workflow: "Workflow", task: "Task"):
        """
        Create a new process from a dictionary.

        :param data: The dictionary to create the process from.
        :param workflow: The workflow the process belongs to.
        :param task: The task the process belongs to.
        """

        for key, type in [
            ("arguments", list),
            ("environment", list),
            ("image", str),
            ("mount_namespace", int),
            ("resource_group", int),
            ("pid_namespace", int),
            ("working_directory", str),
            ("descriptors", dict),
        ]:
            if key not in data:
                raise WorkflowParsingError(
                    f"Failed parsing process.",
                    ParsingFailedOn.PROCESS,
                    f"Missing key '{key}' in process data.",
                )
            if not isinstance(data[key], type):
                raise WorkflowParsingError(
                    f"Failed parsing process.",
                    ParsingFailedOn.PROCESS,
                    f"Key '{key}' in process data is not of type {type.__name__}.",
                )
        if "start_after" in data and not isinstance(data["start_after"], list):
            raise WorkflowParsingError(
                f"Failed parsing process.",
                ParsingFailedOn.PROCESS,
                "Key 'start_after' in process data is not of type list.",
            )

        env = {}
        for var in data["environment"]:
            if "=" not in var:
                raise WorkflowParsingError(
                    f"Failed parsing process.",
                    ParsingFailedOn.PROCESS,
                    f"Environment variable '{var}' does not contain an '=' sign.",
                )
            key, value = var.split("=", 1)
            env[key] = value

        try:
            mount_namespace = task.mountnamespace_manager.get_by_id(data["mount_namespace"])
        except IndexError:
            raise WorkflowParsingError(
                f"Failed parsing process.",
                ParsingFailedOn.PROCESS,
                f"Mount namespace with ID {data['mount_namespace']} not found.",
            )
        try:
            resource_group = task.resource_group_manager.get_by_id(data["resource_group"])
        except IndexError:
            raise WorkflowParsingError(
                f"Failed parsing process.",
                ParsingFailedOn.PROCESS,
                f"Resource group with ID {data['resource_group']} not found.",
            )

        process = cls(
            workflow,
            task,
            data["arguments"],
            env,
            data["image"],
            mount_namespace,
            resource_group,
            data["pid_namespace"],
            data["working_directory"],
            data.get("start_after", []),
        )
        process.descriptor_manager.from_json(data["descriptors"])

        return process

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the process with the given replacements.

        :param dict[str, str] replacements: The replacements to make.
        """
        for key, value in replacements.items():
            if key in self.image:
                self.image = self.image.replace(key, value)
            if key in self.arguments:
                self.arguments = [arg.replace(key, value) for arg in self.arguments]
            for _, desc in self.descriptor_manager.items():
                desc.replace_templates(replacements)
