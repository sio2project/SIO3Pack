from sio3pack.workflow.execution.stream import Stream


class DescriptorManager:
    """
    A class to manage file descriptors and their associated streams.

    :param ObjectsManager objects_manager: The objects manager.
    :param FilesystemManager filesystem_manager: The filesystem manager.
    """

    def __init__(self, objects_manager: "ObjectsManager", filesystem_manager: "FilesystemManager"):
        """
        Initialize the descriptor manager.

        :param ObjectsManager objects_manager: The objects manager.
        :param FilesystemManager filesystem_manager: The filesystem manager.
        """
        self.objects_manager = objects_manager
        self.filesystem_manager = filesystem_manager
        self.descriptors: dict[int, Stream] = {}

    def add_descriptor(self, fd: int, stream: Stream):
        """
        Add a stream to the descriptor manager.

        :param int fd: The file descriptor.
        :param Stream stream: The stream to add.
        """
        self.descriptors[int(fd)] = stream

    def from_json(self, data: dict):
        """
        Load the descriptor manager from a JSON-serializable dictionary.

        :param dict data: The JSON-serializable dictionary to load from.
        """
        for fd, stream_data in data.items():
            stream = Stream.from_json(stream_data, self.objects_manager, self.filesystem_manager)
            self.add_descriptor(int(fd), stream)

    def to_json(self) -> dict:
        """
        Convert the descriptor manager to a JSON-serializable dictionary.
        """
        # Convert the fd numbers to strings, since in JSON keys cant be ints.
        return {str(fd): stream.to_json() for fd, stream in self.descriptors.items()}
