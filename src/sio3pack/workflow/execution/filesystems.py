from sio3pack.workflow.object import Object


class Filesystem:
    """
    A base class to represent a filesystem.

    :param int id: The id of the filesystem in the task.
    """

    def __init__(self, id: int):
        """
        Represent a filesystem.
        :param id: The id of the filesystem.
        """
        self.id = id

    @classmethod
    def from_json(cls, data: dict, id: int, workflow: "Workflow"):
        """
        Create a new filesystem from a dictionary.

        :param dict data: The dictionary to create the filesystem from.
        :param int id: The id of the filesystem.
        :param Workflow workflow: The workflow the filesystem belongs to.
        """
        return NotImplementedError()

    def to_json(self) -> dict:
        """
        Convert the filesystem to a dictionary.

        :return: The dictionary representation of the filesystem.
        """
        return NotImplementedError()


class ImageFilesystem(Filesystem):
    """
    A class to represent an image filesystem.
    An image can be for example a g++ compilator, a python interpreter, etc.

    :param int id: The id of the image filesystem.
    :param str image: The image to use.
    :param str path: The path to the image. If None, the path is "".
    """

    def __init__(self, id: int, image: str, path: str = None):
        """
        Represent an image filesystem.

        :param id: The id of the image filesystem.
        :param image: The image to use.
        :param path: The path to the image. If None, the path is ""
        """
        super().__init__(id)
        self.image = image
        self.path = path or ""

    def __str__(self):
        return f'<ImageFilesystem {self.image} path="{self.path}">'

    @classmethod
    def from_json(cls, data: dict, id: int, workflow: "Workflow") -> "ImageFilesystem":
        """
        Create a new image filesystem from a dictionary.

        :param dict data: The dictionary to create the image filesystem from.
        :param id id: The id of the image filesystem.
        :param Workflow workflow: The workflow the image filesystem belongs to.
        """
        return cls(id, data["image"], data["path"])

    def to_json(self) -> dict:
        """
        Convert the image filesystem to a dictionary.

        :return: The dictionary representation of the image filesystem.
        """
        return {"type": "image", "image": self.image, "path": self.path}


class EmptyFilesystem(Filesystem):
    def __init__(self, id: int):
        """
        Represent an empty filesystem. Can be used as tmpfs.
        :param id: The id of the empty filesystem.
        """
        super().__init__(id)

    def __str__(self):
        return "<EmptyFilesystem>"

    @classmethod
    def from_json(cls, data: dict, id: int, workflow: "Workflow"):
        """
        Create a new empty filesystem from a dictionary.
        :param data: The dictionary to create the empty filesystem from.
        :param id: The id of the empty filesystem.
        :param workflow: The workflow the empty filesystem belongs to.
        """
        return cls(id)

    def to_json(self) -> dict:
        """
        Convert the empty filesystem to a dictionary.
        """
        return {"type": "empty"}


class ObjectFilesystem(Filesystem):
    def __init__(self, id: int, object: Object, workflow: "Workflow"):
        """
        Represent an object filesystem.
        :param id: The id of the object filesystem.
        :param object: The object to use.
        :param workflow: The workflow the object belongs to.
        """
        super().__init__(id)
        self.object = object

    def __str__(self):
        return f"<ObjectFilesystem {self.object.handle}>"

    @classmethod
    def from_json(cls, data: dict, id: int, workflow: "Workflow"):
        """
        Create a new object filesystem from a dictionary.
        :param data: The dictionary to create the object filesystem from.
        :param id: The id of the object filesystem.
        :param workflow: The workflow the object filesystem belongs to.
        """
        return cls(id, workflow.objects_manager.get_or_create_object(data["handle"]), workflow)

    def to_json(self) -> dict:
        """
        Convert the object filesystem to a dictionary.
        """
        return {
            "type": "object",
            "handle": self.object.handle,
        }


class FilesystemManager:
    def __init__(self, task: "Task"):
        """
        Create a new filesystem manager.
        :param task: The task the filesystem manager belongs to.
        """
        self.filesystems: list[Filesystem] = []
        self.id = 0
        self.task = task

    def from_json(self, data: list[dict], workflow: "Workflow"):
        """
        Create filesystems from a list of dictionaries.
        :param data: The list of dictionaries to create the filesystems from.
        :param workflow: The workflow the filesystems belong to.
        """
        for fs in data:
            if fs["type"] == "image":
                self.filesystems.append(ImageFilesystem.from_json(fs, self.id, workflow))
            elif fs["type"] == "empty":
                self.filesystems.append(EmptyFilesystem.from_json(fs, self.id, workflow))
            elif fs["type"] == "object":
                self.filesystems.append(ObjectFilesystem.from_json(fs, self.id, workflow))
            self.id += 1

    def to_json(self) -> list[dict]:
        """
        Convert the filesystems to a list of dictionaries.
        """
        return [fs.to_json() for fs in self.filesystems]

    def get_by_id(self, id: int) -> Filesystem:
        """
        Get a filesystem by id.
        :param id: The id of the filesystem.
        """
        return self.filesystems[id]

    def add(self, filesystem: Filesystem):
        """
        Add a filesystem to the manager.
        :param filesystem: The filesystem to add.
        """
        self.filesystems.append(filesystem)
        self.id += 1
