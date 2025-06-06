from enum import Enum

from sio3pack.exceptions.general import SIO3PackException


class WorkflowCreationError(SIO3PackException):
    """
    Raised when there is an error creating a workflow.
    """


class ParsingFailedOn(Enum):
    """
    Enum to represent the part of the workflow that failed to parse.
    """

    JSON = "json"
    WORKFLOW = "workflow"
    TASK = "task"
    CHANNEL = "channel"
    FILESYSTEM = "filesystem"
    MOUNT_NAMESPACE = "mount_namespace"
    MOUNT_POINT = "mount_point"
    RESOURCE_GROUP = "resource_group"
    PROCESS = "process"
    STREAM = "stream"


class WorkflowParsingError(SIO3PackException):
    """
    Raised when there is an error parsing a workflow configuration.

    :param str message: A short description of the error.
    :param ParsingFailedOn failed_on: The part of the workflow that failed to parse.
    :param str extra_msg: Additional message to append to the error message.
    :param dict data: Additional data related to the error.
    :param str full_message: A full message describing the error, if available.
    """

    def __init__(
        self,
        message: str,
        failed_on: ParsingFailedOn,
        extra_msg: str = None,
        data: dict = None,
        full_message: str = None,
    ):
        """
        Initialize the WorkflowParsingError.

        :param str message: A short description of the error.
        :param ParsingFailedOn failed_on: The part of the workflow that failed to parse.
        :param str extra_msg: Additional message to append to the error message.
        :param dict data: Additional data related to the error.
        :param str full_message: A full message describing the error, if available.
        """
        super().__init__(message)
        self.message = message
        self.failed_on = failed_on
        self.extra_msg = extra_msg
        self._full_message = full_message
        self.data = data or {}

    def set_data(self, key: str, value: str):
        """
        Set additional data for the exception.

        :param key: The key for the data.
        :param value: The value for the data.
        """
        self.data[key] = value

    def _generate_full_message(self):
        """
        Generate a full message for the exception if not provided.
        """

        def task_name():
            msg = f"task {self.data['task_index']}"
            if "task_name" in self.data:
                msg += f" ({self.data['task_name']})"
            return msg

        msg = None
        if self.failed_on == ParsingFailedOn.WORKFLOW:
            msg = f"Workflow parsing failed while parsing top-level workflow definition."
        elif self.failed_on == ParsingFailedOn.TASK:
            msg = f"Workflow parsing failed while parsing {task_name()}."
        elif self.failed_on == ParsingFailedOn.CHANNEL:
            msg = f"Workflow parsing failed while parsing channel configuration {self.data['channel_index']} for {task_name()}."
        elif self.failed_on == ParsingFailedOn.FILESYSTEM:
            msg = f"Workflow parsing failed while parsing filesystem configuration {self.data['filesystem_index']} for {task_name()}."
        elif self.failed_on == ParsingFailedOn.MOUNT_NAMESPACE:
            msg = f"Workflow parsing failed while parsing mount namespace {self.data['mount_namespace_index']} for {task_name()}."
        elif self.failed_on == ParsingFailedOn.MOUNT_POINT:
            msg = f"Workflow parsing failed while parsing mount point {self.data['mountpoint_index']} for mount namespace {self.data['mount_namespace_index']} in {task_name()}."
        elif self.failed_on == ParsingFailedOn.RESOURCE_GROUP:
            msg = f"Workflow parsing failed while parsing resource group {self.data['resource_group_index']} for {task_name()}."
        elif self.failed_on == ParsingFailedOn.PROCESS:
            msg = f"Workflow parsing failed while parsing process {self.data['process_index']} for {task_name()}."
        elif self.failed_on == ParsingFailedOn.STREAM:
            msg = f"Workflow parsing failed while parsing stream {self.data['fd']} for process {self.data['process_index']} for {task_name()}."

        if msg and self.extra_msg:
            msg += " " + self.extra_msg
        return msg
