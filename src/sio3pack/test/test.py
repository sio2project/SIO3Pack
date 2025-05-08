from sio3pack.files import File


class Test:
    """
    Represents an input and output test.
    """

    def __init__(self, test_name: str, test_id: str, in_file: File, out_file: File, group: str):
        self.test_name = test_name
        self.test_id = test_id
        self.in_file = in_file
        self.out_file = out_file
        self.group = group
