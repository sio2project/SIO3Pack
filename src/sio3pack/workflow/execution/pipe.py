class Pipe:
    def __init__(self, buffer_size: int = 1048576, file_buffer_size: int = 1073741824, limit: int = 2147483648):
        """
        Create a new pipe config.
        :param buffer_size: The buffer size for the pipe.
        :param file_buffer_size: The buffer size for files.
        :param limit: The limit for the pipe.
        """
        self.buffer_size = buffer_size
        self.file_buffer_size = file_buffer_size
        self.limit = limit

    @classmethod
    def from_json(cls, data: dict):
        """
        Create a new pipe config from a dictionary.
        :param data: The dictionary to create the pipe config from.
        """
        return cls(data["buffer_size"], data["file_buffer_size"], data["limit"])

    def to_json(self) -> dict:
        """
        Convert the pipe config to a dictionary.
        """
        return {"buffer_size": self.buffer_size, "file_buffer_size": self.file_buffer_size, "limit": self.limit}
