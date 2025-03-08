from sio3pack.workflow.execution.mount_namespace import MountNamespace, MountNamespaceManager
from sio3pack.workflow.execution.resource_group import ResourceGroup, ResourceGroupManager


class Process:
    def __init__(self, arguments: [str] = None, environment: dict = None, image: str = "",
                 mount_namespace: MountNamespace = None, resource_group: ResourceGroup = None, pid_namespace: int = 0,
                 working_directory: str = "/"):
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

    def to_dict(self):
        return {
            'arguments': self.arguments,
            'environment': [f'{key}={value}' for key, value in self.environment.items()],
            'image': self.image,
            'mount_namespace': self.mount_namespace.id,
            'resource_group': self.resource_group.id,
            'pid_namespace': self.pid_namespace,
            'working_directory': self.working_directory
        }

    @classmethod
    def from_dict(cls, data: dict, mountnamespace_manager: MountNamespaceManager, resource_group_manager: ResourceGroupManager):
        env = {}
        for var in data['environment']:
            key, value = var.split('=', 1)
            env[key] = value
        return cls(data['arguments'], env, data['image'], mountnamespace_manager.get_by_id(data['mount_namespace']),
                       resource_group_manager.get_by_id(data['resource_group']), data['pid_namespace'], data['working_directory'])
