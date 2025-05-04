class Channel:
    """
    A configuration of a channel. A channel is a connection between two pipes.

    :param int buffer_size: The maximum amount of data stored in the channel that has been written by
      the writer, but not yet read by the reader. This value must be positive.
    :param int source_pipe: The pipe this channel will be reading from.
    :param int target_pipe: The pipe this channel will be writing to.
    :param int file_buffer_size: Controls whether this channel is backed by a file on the disk.
      A larger buffer may then be allocated on the disk.
    :param int limit: Limits the maximum amount of data sent through the channel.
    """

    def __init__(
        self, buffer_size: int, source_pipe: int, target_pipe: int, file_buffer_size: int = None, limit: int = None
    ):
        """
        A configuration of a channel. A channel is a connection between two pipes.

        :param int buffer_size: The maximum amount of data stored in the channel that has been written by
          the writer, but not yet read by the reader. This value must be positive.
        :param int source_pipe: The pipe this channel will be reading from.
        :param int target_pipe: The pipe this channel will be writing to.
        :param int file_buffer_size: Controls whether this channel is backed by a file on the disk.
          A larger buffer may then be allocated on the disk.
        :param int limit: Limits the maximum amount of data sent through the channel.
        """
        if buffer_size <= 0:
            raise ValueError("Buffer size must be positive")
        self.buffer_size = buffer_size
        self.source_pipe = source_pipe
        self.target_pipe = target_pipe
        self.file_buffer_size = file_buffer_size
        self.limit = limit

    @classmethod
    def from_json(cls, data: dict) -> "Channel":
        """
        Create a new channel from a dictionary.

        :param dict data: The dictionary to create the channel from.
        """

        return cls(
            data["buffer_size"],
            data["source_pipe"],
            data["target_pipe"],
            data.get("file_buffer_size"),
            data.get("limit"),
        )

    def to_json(self) -> dict:
        """
        Convert the channel to a dictionary.
        """

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
