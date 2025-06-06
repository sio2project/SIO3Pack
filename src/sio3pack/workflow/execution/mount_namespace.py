from sio3pack.exceptions import ParsingFailedOn, WorkflowParsingError
from sio3pack.workflow.execution.filesystems import Filesystem, FilesystemManager


class Mountpoint:
    """
    A class to represent a mountpoint.

    :param "Filesystem" source: The source filesystem.
    :param str target: The target path in the filesystem.
    :param bool writable: Whether the mountpoint is writable or not.
    :param int capacity: The capacity of the mountpoint. If None, the capacity is unlimited.
    """

    def __init__(self, source: "Filesystem", target: str, writable: bool = False, capacity: int | None = None):
        """
        Represent a mountpoint.

        :param source: The source filesystem.
        :param target: The target path in the filesystem.
        :param writable: Whether the mountpoint is writable or not.
        :param capacity: The capacity of the mountpoint. If None, the capacity is unlimited.
        """
        self.source = source
        self.target = target
        self.writable = writable
        self.capacity = capacity

    @classmethod
    def from_json(cls, data: dict, filesystem_manager: FilesystemManager) -> "Mountpoint":
        """
        Create a new mountpoint from a dictionary.

        :param dict data: The dictionary to create the mountpoint from.
        :param FilesystemManager filesystem_manager: The filesystem manager to use.
        """
        for key in ["source", "target", "writable"]:
            if key not in data:
                raise WorkflowParsingError(
                    "Failed parsing mount point",
                    ParsingFailedOn.MOUNT_POINT,
                    f"Missing key '{key}' in mount point data.",
                )
        for key, type in [("source", int), ("target", str), ("writable", bool), ("capacity", int)]:
            if key in data and not isinstance(data[key], type):
                raise WorkflowParsingError(
                    "Failed parsing mount point",
                    ParsingFailedOn.MOUNT_POINT,
                    f"Key '{key}' in mount point data is not of type {type.__name__}.",
                )
        if not filesystem_manager.has_by_id(int(data["source"])):
            raise WorkflowParsingError(
                "Failed parsing mount point",
                ParsingFailedOn.MOUNT_POINT,
                f"Source filesystem with id {data['source']} not found.",
            )

        return cls(
            filesystem_manager.get_by_id(int(data["source"])), data["target"], data["writable"], data.get("capacity")
        )

    def to_json(self) -> dict:
        """
        Convert the mountpoint to a dictionary.
        """
        res = {"source": self.source.id, "target": self.target, "writable": self.writable}
        if self.capacity is not None:
            res["capacity"] = self.capacity
        return res


class MountNamespace:
    """
    A class to represent a mount namespace.
    It can mount :class:`Mountpoint` instances in the target filesystem.

    :param int id: The id of the mount namespace.
    :param list[Mountpoint] mountpoints: The mountpoints in the mount namespace.
    """

    def __init__(self, mountpoints: list[Mountpoint] = None, root: int = 0, id: int = None):
        self.mountpoints = mountpoints or []
        self.root = root
        self.id = id

    def _set_id(self, id: int):
        """
        Set the id of the mount namespace. Should only be used by the MountNamespaceManager.

        :param id: The id to set.
        """
        self.id = id

    @classmethod
    def from_json(cls, data: dict, id: int, filesystem_manager: FilesystemManager):
        """
        Create a new mount namespace from a dictionary.
        :param data: The dictionary to create the mount namespace from.
        :param id: The id of the mount namespace.
        :param filesystem_manager: The filesystem manager to use.
        """
        for key in ["mountpoints", "root"]:
            if key not in data:
                raise WorkflowParsingError(
                    "Failed parsing mount namespace",
                    ParsingFailedOn.MOUNT_NAMESPACE,
                    f"Missing key '{key}' in mount namespace data.",
                    data={"mount_namespace_index": str(id)},
                )
        for key, type in [("mountpoints", list), ("root", int)]:
            if not isinstance(data[key], type):
                raise WorkflowParsingError(
                    "Failed parsing mount namespace",
                    ParsingFailedOn.MOUNT_NAMESPACE,
                    f"Key '{key}' in mount namespace data is not of type {type.__name__}.",
                    data={"mount_namespace_index": str(id)},
                )

        mountpoints = []
        for i, mountpoint in enumerate(data["mountpoints"]):
            try:
                mountpoints.append(Mountpoint.from_json(mountpoint, filesystem_manager))
            except WorkflowParsingError as e:
                e.set_data("mount_namespace_index", str(id))
                e.set_data("mountpoint_index", str(i))
                raise e

        return cls(
            mountpoints,
            data["root"],
            id,
        )

    def to_json(self) -> dict:
        """
        Convert the mount namespace to a dictionary.
        """
        return {"mountpoints": [mountpoint.to_json() for mountpoint in self.mountpoints], "root": self.root}

    def add_mountpoint(self, mountpoint: Mountpoint):
        """
        Add a mountpoint to the mount namespace.

        :param mountpoint: The mountpoint to add.
        """
        self.mountpoints.append(mountpoint)


class MountNamespaceManager:
    def __init__(self, task: "Task", filesystem_manager: "FilesystemManager"):
        """
        Create a new mount namespace manager.

        :param Task task: The task the mount namespace manager belongs to.
        :param FilesystemManager filesystem_manager: Workflow's filesystem manager.
        """
        self.mount_namespaces: list[MountNamespace] = []
        self.id = 0
        self.task = task
        self.filesystem_manager = filesystem_manager

    def from_json(self, data: list[dict]):
        """
        Create a new mount namespace manager from a list of dictionaries.

        :param data: The list of dictionaries to create the mount namespace manager from.
        """
        for i, mount_namespace in enumerate(data):
            try:
                self.add(MountNamespace.from_json(mount_namespace, self.id, self.filesystem_manager))
            except WorkflowParsingError as e:
                e.set_data("mn_index", str(i))
                raise e
            self.id += 1

    def add(self, mount_namespace: MountNamespace):
        """
        Add a mount namespace to the manager.

        :param MountNamespace mount_namespace: The mount namespace to add.
        """
        mount_namespace._set_id(self.id)
        self.mount_namespaces.append(mount_namespace)

    def get_by_id(self, id: int) -> MountNamespace:
        """
        Get a mount namespace by its id.

        :param id: The id of the mount namespace.
        """
        return self.mount_namespaces[id]

    def to_json(self) -> list[dict]:
        """
        Convert the mount namespace manager to a dictionary.
        """
        return [mount_namespace.to_json() for mount_namespace in self.mount_namespaces]

    def len(self) -> int:
        """
        Get the number of mount namespaces.
        """
        return len(self.mount_namespaces)
