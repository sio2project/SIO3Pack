from enum import Enum

from sio3pack.workflow import Object
from sio3pack.workflow.execution import Filesystem
from sio3pack.workflow.execution.filesystems import FilesystemManager
from sio3pack.workflow.object import ObjectsManager


class StreamType(Enum):
    FILE = "file"
    NULL = "null"
    OBJECT_READ = "object_read"
    OBJECT_WRITE = "object_write"
    PIPE_READ = "pipe_read"
    PIPE_WRITE = "pipe_write"


class FileMode(Enum):
    READ = "read"
    READ_WRTIE = "read_write"
    READ_WRITE_APPEND = "read_write_append"
    READ_WRITE_TRUNCATE = "read_write_truncate"
    WRITE = "write"
    WRITE_APPEND = "write_append"
    WRITE_TRUNCATE = "write_truncate"


class Stream:
    def __init__(self, type: StreamType):
        self.type = type

    @classmethod
    def from_json(cls, data: dict, objects_manager: ObjectsManager, filesystem_manager: FilesystemManager):
        type = StreamType(data.get("type"))
        if type == StreamType.FILE:
            return FileStream.from_json(filesystem_manager, data)
        elif type == StreamType.NULL:
            return NullStream.from_json(data)
        elif type in (StreamType.OBJECT_READ, StreamType.OBJECT_WRITE):
            return ObjectStream.from_json(data, objects_manager)
        elif type in (StreamType.PIPE_READ, StreamType.PIPE_WRITE):
            return PipeStream.from_json(data)
        else:
            raise ValueError(f"Unknown stream type: {type}")

    def to_json(self) -> dict:
        raise NotImplementedError("Subclasses must implement to_json method")


class FileStream(Stream):
    def __init__(self, filesystem: Filesystem, path: str, mode: FileMode):
        super().__init__(StreamType.FILE)
        self.filesystem = filesystem
        self.path = path
        self.mode = mode

    @classmethod
    def from_json(cls, filesystem_manager: FilesystemManager, data: dict):
        return cls(
            filesystem_manager.get_by_id(data.get("filesystem")),
            data.get("path"),
            FileMode(data.get("mode")),
        )

    def to_json(self) -> dict:
        return {
            "type": self.type.value,
            "filesystem": self.filesystem.id,
            "path": self.path,
            "mode": self.mode.value,
        }


class NullStream(Stream):
    def __init__(self):
        super().__init__(StreamType.NULL)

    @classmethod
    def from_json(cls, data: dict):
        return cls()

    def to_json(self) -> dict:
        return {
            "type": self.type.value,
        }


class ObjectStream(Stream):
    def __init__(self, type: StreamType, object: Object):
        if type not in (StreamType.OBJECT_READ, StreamType.OBJECT_WRITE):
            raise ValueError("Invalid stream type for ObjectStream")
        super().__init__(type)
        self.object = object

    @classmethod
    def from_json(cls, data: dict, objects_manager: ObjectsManager):
        return cls(
            StreamType(data.get("type")),
            objects_manager.get_or_create_object(data.get("handle")),
        )

    def to_json(self) -> dict:
        """
        Convert the object stream to a dictionary.
        """
        return {
            "type": self.type.value,
            "handle": self.object.handle,
        }


class ObjectReadStream(ObjectStream):
    def __init__(self, object: Object):
        super().__init__(StreamType.OBJECT_READ, object)


class ObjectWriteStream(ObjectStream):
    def __init__(self, object: Object):
        super().__init__(StreamType.OBJECT_WRITE, object)   


class PipeStream(Stream):
    def __init__(self, type: StreamType, pipe_index: int):
        if type not in (StreamType.PIPE_READ, StreamType.PIPE_WRITE):
            raise ValueError("Invalid stream type for PipeStream")
        super().__init__(type)
        self.pipe_index = pipe_index

    @classmethod
    def from_json(cls, data: dict):
        return cls(StreamType(data.get("type")), data.get("pipe"))

    def to_json(self) -> dict:
        """
        Convert the pipe stream to a dictionary.
        """
        return {
            "type": self.type.value,
            "pipe": self.pipe_index,
        }


class PipeReadStream(PipeStream):
    def __init__(self, pipe_index: int):
        super().__init__(StreamType.PIPE_READ, pipe_index)


class PipeWriteStream(PipeStream):
    def __init__(self, pipe_index: int):
        super().__init__(StreamType.PIPE_WRITE, pipe_index)
