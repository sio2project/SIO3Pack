from sio3pack.workflow.execution.descriptors import DescriptorManager
from sio3pack.workflow.execution.mount_namespace import MountNamespace
from sio3pack.workflow.execution.resource_group import ResourceGroup


class Process:
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
    ):
        """
        Represent a process.
        :param arguments: The arguments of the process.
        :param environment: The environment of the process.
        :param image: The image of the process.
        :param mount_namespace: The mount namespace of the process.
        :param resource_group: The resource group of the process.
        :param working_directory: The working directory of the process.
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

    def to_json(self) -> dict:
        return {
            "arguments": self.arguments,
            "environment": [f"{key}={value}" for key, value in self.environment.items()],
            "image": self.image,
            "mount_namespace": self.mount_namespace.id,
            "resource_group": self.resource_group.id,
            "pid_namespace": self.pid_namespace,
            "working_directory": self.working_directory,
            "descriptors": self.descriptor_manager.to_json(),
        }

    @classmethod
    def from_json(cls, data: dict, workflow: "Workflow", task: "Task"):
        env = {}
        for var in data["environment"]:
            key, value = var.split("=", 1)
            env[key] = value
        process = cls(
            workflow,
            task,
            data["arguments"],
            env,
            data["image"],
            task.mountnamespace_manager.get_by_id(data["mount_namespace"]),
            task.resource_group_manager.get_by_id(data["resource_group"]),
            data["pid_namespace"],
            data["working_directory"],
        )
        process.descriptor_manager.from_json(data["descriptors"])
        return process

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the process with the given replacements.
        :param replacements: The replacements to make.
        """
        for key, value in replacements.items():
            if key in self.image:
                self.image = self.image.replace(key, value)
            if key in self.arguments:
                self.arguments = [arg.replace(key, value) for arg in self.arguments]
            for _, desc in self.descriptor_manager.items():
                desc.replace_templates(replacements)
