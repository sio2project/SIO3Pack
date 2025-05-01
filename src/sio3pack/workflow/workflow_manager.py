import json
from enum import Enum

from sio3pack.files import File
from sio3pack.test import Test
from sio3pack.workflow.workflow_op import WorkflowOperation
from sio3pack.workflow.workflow import Workflow


class UnpackStage(Enum):
    NONE = 0
    GEN_TESTS = 1
    VERIFY = 2
    FINISHED = 3


class WorkflowManager:
    @classmethod
    def from_file(cls, file: File):
        workflows = {}
        content = json.loads(file.read())
        for name, graph in content.items():
            workflows[name] = Workflow.from_json(graph)
        return cls(workflows)

    def __init__(self, package: "Package", workflows: dict[str, Workflow]):
        self.package = package
        self.workflows = workflows
        self._has_test_gen = False
        self._has_verify = False
        self._unpack_stage = UnpackStage.NONE

    def get(self, name: str) -> Workflow:
        """
        Get the workflow with the given name. If
        the workflow does not exist, return default
        workflow for this name from self.get_default.

        :param name: The name of the workflow.
        :return: The workflow with the given name.
        """
        if name not in self.workflows:
            return self.get_default(name)
        return self.workflows[name]

    def get_default(self, name: str) -> Workflow:
        """
        Get the default workflow for the given name.
        This method should be overridden by subclasses
        to provide the default workflow for the given name.

        :param name: The name of the workflow.
        :return: The default workflow for the given name.
        """
        raise NotImplementedError(f"Default workflow for {name} not implemented.")

    def get_prog_files(self) -> list[str]:
        """
        Get all program files used in all graphs.
        """
        # TODO: implement this
        raise NotImplementedError

    def _get_generate_tests_workflows(self, data: dict) -> tuple[Workflow, bool]:
        raise NotImplementedError

    def _get_verify_workflows(self, data: dict) -> tuple[Workflow, bool]:
        raise NotImplementedError

    def _get_unpack_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Get all workflows that are used to unpack the given data.
        """
        if self._unpack_stage == UnpackStage.GEN_TESTS:
            workflow, last = self._get_generate_tests_workflows(data)
            if last:
                if self._has_verify:
                    self._unpack_stage = UnpackStage.VERIFY
                else:
                    self._unpack_stage = UnpackStage.FINISHED
        elif self._unpack_stage == UnpackStage.VERIFY:
            workflow, last = self._get_verify_workflows(data)
            if last:
                self._unpack_stage = UnpackStage.FINISHED
        else:
            raise ValueError(f"Invalid unpack stage: {self._unpack_stage}")
        return workflow, self._unpack_stage == UnpackStage.FINISHED

    def get_unpack_operation(self, has_test_gen: bool, has_verify: bool, return_func: callable = None) -> WorkflowOperation:
        self._has_test_gen = has_test_gen
        self._has_verify = has_verify
        if has_test_gen:
            self._unpack_stage = UnpackStage.GEN_TESTS
        elif has_verify:
            self._unpack_stage = UnpackStage.VERIFY
        else:
            # TODO: this. maybe return empty WorkflowOperation
            raise NotImplementedError
        return WorkflowOperation(self._get_unpack_workflows, return_results=(return_func is not None), return_results_func=return_func)

    def get_run_operation(self, program: File, tests: list[Test] | None = None, return_func: callable = None) -> WorkflowOperation:
        raise NotImplementedError
