class Channel:
    def __init__(self, buffer_size: int, source_pipe: int, target_pipe: int, file_buffer_size: int = None, limit: int = None):
        """
        Create a new channel.
        :param buffer_size: The size of the buffer.
        :param source_pipe: The source pipe index.
        :param target_pipe: The target pipe index.
        :param file_buffer_size: The size of the file buffer.
        :param limit: The limit of the channel.
        """
        self.buffer_size = buffer_size
        self.source_pipe = source_pipe
        self.target_pipe = target_pipe
        self.file_buffer_size = file_buffer_size
        self.limit = limit

    @classmethod
    def from_json(cls, data: dict) -> "Channel":
        """
        Create a new channel from a dictionary.
        :param data: The dictionary to create the channel from.
        """
        return cls(
            data["buffer_size"],
            data["source_pipe"],
            data["target_pipe"],
            data.get("file_buffer_size"),
            data.get("limit"),
        )

    def to_json(self) -> dict:
        res = {
            "buffer_size": self.buffer_size,
            "source_pipe": self.source_pipe,
            "target_pipe": self.target_pipe,
        }
        if self.file_buffer_size:
            res["file_buffer_size"] = self.file_buffer_size
        if self.limit:
            res["limit"] = self.limit
        return res
