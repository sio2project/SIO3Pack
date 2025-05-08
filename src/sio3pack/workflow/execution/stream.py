from enum import Enum

from sio3pack.workflow import Object
from sio3pack.workflow.execution.filesystems import Filesystem, FilesystemManager
from sio3pack.workflow.object import ObjectsManager


class StreamType(Enum):
    """
    Enum representing the type of stream.
    """

    FILE = "file"
    NULL = "null"
    OBJECT_READ = "object_read"
    OBJECT_WRITE = "object_write"
    PIPE_READ = "pipe_read"
    PIPE_WRITE = "pipe_write"


class FileMode(Enum):
    """
    Enum representing the mode of a file stream.
    """

    READ = "read"
    READ_WRITE = "read_write"
    READ_WRITE_APPEND = "read_write_append"
    READ_WRITE_TRUNCATE = "read_write_truncate"
    WRITE = "write"
    WRITE_APPEND = "write_append"
    WRITE_TRUNCATE = "write_truncate"


class Stream:
    """
    Base class for all streams.

    :param StreamType type: The type of the stream.
    """

    def __init__(self, type: StreamType):
        """
        Initialize the stream.

        :param StreamType type: The type of the stream.
        """
        self.type = type

    @classmethod
    def from_json(cls, data: dict, objects_manager: ObjectsManager, filesystem_manager: FilesystemManager) -> "Stream":
        """
        Create a stream from a JSON-serializable dictionary.

        :param dict data: The JSON-serializable dictionary to create the stream from.
        :param ObjectsManager objects_manager: The objects manager.
        :param FilesystemManager filesystem_manager: The filesystem manager.
        """

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

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the stream with the given replacements.
        This method is a no-op for streams that do not support template replacement.
        """
        pass


class FileStream(Stream):
    """
    Class representing a file stream. A file will be opened
    and passed to the process as a file descriptor.

    :param Filesystem filesystem: The filesystem to use.
    :param str path: The path to the file.
    :param FileMode mode: The mode to open the file in.
    """

    def __init__(self, filesystem: Filesystem, path: str, mode: FileMode):
        super().__init__(StreamType.FILE)
        self.filesystem = filesystem
        self.path = path
        self.mode = mode

    @classmethod
    def from_json(cls, filesystem_manager: FilesystemManager, data: dict) -> "FileStream":
        """
        Create a file stream from a JSON-serializable dictionary.

        :param FilesystemManager filesystem_manager: The filesystem manager.
        :param dict data: The JSON-serializable dictionary to create the file stream from.
        """
        return cls(
            filesystem_manager.get_by_id(data.get("filesystem")),
            data.get("path"),
            FileMode(data.get("mode")),
        )

    def to_json(self) -> dict:
        """
        Convert the file stream to a dictionary.

        :return: The dictionary representation of the file stream.
        """

        return {
            "type": self.type.value,
            "filesystem": self.filesystem.id,
            "path": self.path,
            "mode": self.mode.value,
        }


class NullStream(Stream):
    """
    Class representing a null stream.
    """

    def __init__(self):
        super().__init__(StreamType.NULL)

    @classmethod
    def from_json(cls, data: dict) -> "NullStream":
        """
        Create a null stream from a JSON-serializable dictionary.

        :param dict data: The JSON-serializable dictionary to create the null stream from.
        """
        return cls()

    def to_json(self) -> dict:
        """
        Convert the null stream to a dictionary.

        :return: The dictionary representation of the null stream.
        """
        return {
            "type": self.type.value,
        }


class ObjectStream(Stream):
    """
    A base class for object streams. An object stream is a stream that
    reads or writes to an object via a file descriptor.

    :param StreamType type: The type of the stream.
    :param Object object: The object to use.
    """

    def __init__(self, type: StreamType, object: Object):
        if type not in (StreamType.OBJECT_READ, StreamType.OBJECT_WRITE):
            raise ValueError("Invalid stream type for ObjectStream")
        super().__init__(type)
        self.object = object

    @classmethod
    def from_json(cls, data: dict, objects_manager: ObjectsManager) -> "ObjectStream":
        """
        Create an object stream from a JSON-serializable dictionary.

        :param dict data: The JSON-serializable dictionary to create the object stream from.
        """
        cl = ObjectReadStream if StreamType(data.get("type")) == StreamType.OBJECT_READ else ObjectWriteStream
        return cl(
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

    def replace_templates(self, replacements: dict[str, str]):
        """
        Replace strings in the object stream with the given replacements.
        """
        self.object.replace_templates(replacements)
        super().replace_templates(replacements)


class ObjectReadStream(ObjectStream):
    """
    Class representing an object read stream. An object read stream
    is a stream that reads from an object via a file descriptor.

    :param Object object: The object to read from.
    """

    def __init__(self, object: Object):
        """
        Initialize the object read stream.

        :param Object object: The object to read from.
        """
        super().__init__(StreamType.OBJECT_READ, object)


class ObjectWriteStream(ObjectStream):
    """
    Class representing an object write stream. An object write stream
    is a stream that writes to an object via a file descriptor.

    :param Object object: The object to write to.
    """

    def __init__(self, object: Object):
        """
        Initialize the object write stream.

        :param Object object: The object to write to.
        """
        super().__init__(StreamType.OBJECT_WRITE, object)


class PipeStream(Stream):
    """
    A base class for pipe streams. A pipe stream is a stream that
    reads or writes to a pipe via a file descriptor.

    :param StreamType type: The type of the stream.
    :param int pipe_index: The index of the pipe.
    """

    def __init__(self, type: StreamType, pipe_index: int):
        """
        Initialize the pipe stream.

        :param StreamType type: The type of the stream.
        :param int pipe_index: The index of the pipe.
        """
        if type not in (StreamType.PIPE_READ, StreamType.PIPE_WRITE):
            raise ValueError("Invalid stream type for PipeStream")
        super().__init__(type)
        self.pipe_index = pipe_index

    @classmethod
    def from_json(cls, data: dict) -> "PipeStream":
        """
        Create a pipe stream from a JSON-serializable dictionary.

        :param dict data: The JSON-serializable dictionary to create the pipe stream from.
        """
        cl = PipeReadStream if StreamType(data.get("type")) == StreamType.PIPE_READ else PipeWriteStream
        return cl(data.get("pipe"))

    def to_json(self) -> dict:
        """
        Convert the pipe stream to a dictionary.
        """
        return {
            "type": self.type.value,
            "pipe": self.pipe_index,
        }


class PipeReadStream(PipeStream):
    """
    Class representing a pipe read stream. A pipe read stream
    is a stream that reads from a pipe via a file descriptor.

    :param int pipe_index: The index of the pipe.
    """

    def __init__(self, pipe_index: int):
        """
        Initialize the pipe read stream.

        :param int pipe_index: The index of the pipe.
        """
        super().__init__(StreamType.PIPE_READ, pipe_index)


class PipeWriteStream(PipeStream):
    """
    Class representing a pipe write stream. A pipe write stream
    is a stream that writes to a pipe via a file descriptor.

    :param int pipe_index: The index of the pipe.
    """

    def __init__(self, pipe_index: int):
        """
        Initialize the pipe write stream.

        :param int pipe_index: The index of the pipe.
        """
        super().__init__(StreamType.PIPE_WRITE, pipe_index)
