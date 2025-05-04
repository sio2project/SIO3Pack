class ResourceGroup:
    def __init__(
        self,
        cpu_usage_limit: int = 100.0,
        instruction_limit: int = 1e9,
        memory_limit: int = 2147483648,
        oom_terminate_all_tasks: bool = False,
        pid_limit: int = 2,
        swap_limit: int = 0,
        time_limit: int = 1e9,
        id: int = None,
    ):
        """
        Create a new resource group.
        :param id: The id of the resource group.
        :param cpu_usage_limit: The CPU usage limit.
        :param instruction_limit: The instruction usage limit.
        :param memory_limit: The memory limit.
        :param oom_terminate_all_tasks: Whether to terminate all tasks on OOM.
        :param pid_limit: The PID limit.
        :param swap_limit: The swap limit.
        :param time_limit: The time limit.
        """
        self.id = id
        self.cpu_usage_limit = cpu_usage_limit
        self.instruction_limit = instruction_limit
        self.memory_limit = memory_limit
        self.oom_terminate_all_tasks = oom_terminate_all_tasks
        self.pid_limit = pid_limit
        self.swap_limit = swap_limit
        self.time_limit = time_limit

    def _set_id(self, id: int):
        """
        Set the id of the resource group. Should only be used by the ResourceGroupManager.

        :param id: The id to set.
        """
        self.id = id

    def set_limits(self, cpu_usage_limit: int, instruction_limit: int, memory_limit: int, time_limit: int):
        """
        Set the limits of the resource group.
        :param cpu_usage_limit: The CPU usage limit.
        :param instruction_limit: The instruction usage limit.
        :param memory_limit: The memory limit.
        :param time_limit: The time limit.
        """
        self.cpu_usage_limit = cpu_usage_limit
        self.instruction_limit = instruction_limit
        self.memory_limit = memory_limit
        self.time_limit = time_limit

    @classmethod
    def from_json(cls, data: dict, id: int):
        """
        Create a new resource group from a dictionary.
        :param data: The dictionary to create the resource group from.
        :param id: The id of the resource group.
        """
        return cls(
            data["cpu_usage_limit"],
            data["instruction_limit"],
            data["memory_limit"],
            data["oom_terminate_all_tasks"],
            data["pid_limit"],
            data["swap_limit"],
            data["time_limit"],
            id,
        )

    def to_json(self) -> dict:
        """
        Convert the resource group to a dictionary.
        """
        return {
            "cpu_usage_limit": self.cpu_usage_limit,
            "instruction_limit": self.instruction_limit,
            "memory_limit": self.memory_limit,
            "oom_terminate_all_tasks": self.oom_terminate_all_tasks,
            "pid_limit": self.pid_limit,
            "swap_limit": self.swap_limit,
            "time_limit": self.time_limit,
        }


class ResourceGroupManager:
    def __init__(self, task: "Task"):
        """
        Create a new resource group manager.
        :param task: The task the resource group manager belongs to.
        """
        self.resource_groups: list[ResourceGroup] = []
        self.id = 0

    def add(self, resource_group: ResourceGroup):
        """
        Add a resource group to the resource group manager.
        :param resource_group: The resource group to add.
        """
        resource_group._set_id(self.id)
        self.resource_groups.append(resource_group)
        self.id += 1

    def get_by_id(self, id: int) -> ResourceGroup:
        """
        Get a resource group by its id.
        :param id: The id of the resource group to get.
        """
        return self.resource_groups[id]

    def to_json(self) -> list[dict]:
        """
        Convert the resource group manager to a dictionary.
        """
        return [resource_group.to_json() for resource_group in self.resource_groups]

    def from_json(self, data: list[dict]):
        """
        Create a new resource group manager from a list of dictionaries.
        :param data: The list of dictionaries to create the resource group manager from.
        """
        for resource_group in data:
            self.add(ResourceGroup.from_json(resource_group, self.id))
            self.id += 1

    def all(self) -> list[ResourceGroup]:
        """
        Get all resource groups.
        """
        return self.resource_groups
