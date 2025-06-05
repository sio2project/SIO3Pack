from sio3pack.files import File


class Test:
    """
    Represents an input and output test.

    :param str test_name: Name of the test.
    :param str test_id: Unique identifier for the test.
    :param File in_file: Input file for the test.
    :param File out_file: Output file for the test.
    :param str group: Group identifier for the test.
    """

    def __init__(self, test_name: str, test_id: str, in_file: File, out_file: File, group: str):
        self.test_name = test_name
        self.test_id = test_id
        self.in_file = in_file
        self.out_file = out_file
        self.group = group

    def __repr__(self):
        return f"<Test {self.test_name}>"
