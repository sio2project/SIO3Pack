from sio3pack.files import File
from sio3pack.test import Test


class SimpleTest(Test):
    def __init__(
        self,
        file_in: File,
        file_out: File,
        group: str,
        default_mem_limit: int,
        default_time_limit: int,
        mem_limits: dict[str, int],
        time_limits: dict[str, int],
    ):
        super().__init__()
        self.file_in = file_in
        self.file_out = file_out
        self.group = group
        self.default_mem_limit = default_mem_limit
        self.default_time_limit = default_time_limit
        self.mem_limits = mem_limits
        self.time_limits = time_limits
