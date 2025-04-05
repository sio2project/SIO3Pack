from sio3pack.workflow.execution.filesystems import FilesystemManager
from sio3pack.workflow.execution.stream import Stream
from sio3pack.workflow.object import ObjectsManager


class DescriptorManager:
    def __init__(self, objects_manager: ObjectsManager, filesystem_manager: FilesystemManager):
        self.filesystem_manager = filesystem_manager
        self.descriptors: dict[int, Stream] = {}

    def add_descriptor(self, fd: int, stream: Stream):
        """
        Add a stream to the descriptor manager.
        :param fd: The file descriptor.
        :param stream: The stream to add.
        """
        self.descriptors[int(fd)] = stream

    def from_json(self, data: dict, objects_manager: ObjectsManager, filesystem_manager: FilesystemManager):
        for fd, stream_data in data.items():
            stream = Stream.from_json(stream_data, objects_manager, filesystem_manager)
            self.add_descriptor(int(fd), stream)

    def to_json(self) -> dict:
        """
        Convert the descriptor manager to a JSON-serializable dictionary.
        :return: The JSON-serializable dictionary.
        """
        # Convert the fd numbers to strings, since in JSON keys cant be ints.
        return {str(fd): stream.to_json() for fd, stream in self.descriptors.items()}
