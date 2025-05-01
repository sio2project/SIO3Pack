from sio3pack.files import File


class Test:
    """
    Represents an input or output test.
    Represents an input and output test.
    """

    def __init__(self, test_id: str, in_file: File, out_file: File, group: str):
        self.test_id = test_id
        self.in_file = in_file
        self.out_file = out_file
        self.group = group

    pass
