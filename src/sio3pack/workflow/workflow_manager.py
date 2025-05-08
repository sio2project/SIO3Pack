import copy
from enum import Enum
from typing import Any

from sio3pack.files import File
from sio3pack.test import Test
from sio3pack.workflow import ExecutionTask, constants
from sio3pack.workflow.execution import MountNamespace, ObjectWriteStream, Process, ResourceGroup
from sio3pack.workflow.execution.filesystems import ObjectFilesystem
from sio3pack.workflow.execution.mount_namespace import Mountpoint
from sio3pack.workflow.workflow import Workflow
from sio3pack.workflow.workflow_op import WorkflowOperation


class UnpackStage(Enum):
    NONE = 0
    # Compile required files
    COMPILE_FILES = 1
    # Generate tests
    GEN_TESTS = 2
    # Verify tests
    VERIFY = 3
    # Finished
    FINISHED = 4


class WorkflowManager:
    def __init__(self, package: "Package", workflows: dict[str, Any]):
        for name, wf in workflows.items():
            wf = Workflow.from_json(wf)
            workflows[name] = wf

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
        wf = self.workflows[name]
        return copy.deepcopy(wf)

    def all(self) -> dict[str, Workflow]:
        """
        Get all workflows.

        :return: A dictionary of all workflows.
        """
        return self.workflows

    def get_default(self, name: str) -> Workflow:
        """
        Get the default workflow for the given name.
        This method should be overridden by subclasses
        to provide the default workflow for the given name.

        :param name: The name of the workflow.
        :return: The default workflow for the given name.
        """
        if name == "compile_cpp":
            return self._get_compile_cpp_workflow()
        elif name == "compile_python":
            return self._get_compile_python_workflow()
        return None

    def get_prog_files(self) -> list[str]:
        """
        Get all program files used in all graphs.
        """
        # TODO: implement this
        raise NotImplementedError

    def get_compile_file_workflow(self, file: File | str) -> tuple[Workflow, str]:
        """
        A helper function to get a workflow for compiling the given file.
        The file should be a program file, not a test file.
        Returns a tuple of the workflow and the path to the compiled file.
        The files are not added as external or observable objects,
        since they don't have to be.

        :param file: The file (or the path to the file) to compile.
        :return: A tuple of the workflow and the path to the compiled file.
        """
        if isinstance(file, File):
            file = file.path
        exe_path = self.package.get_executable_path(file)
        language = self.package.get_file_language(file)
        wf = self.get(f"compile_{language}")
        file_obj = wf.objects_manager.get_or_create_object(file)
        compiled_obj = wf.objects_manager.get_or_create_object(exe_path)
        wf.replace_templates(
            {
                "<FILE>": file_obj.handle,
                "<OUT>": compiled_obj.handle,
            }
        )
        return wf, exe_path

    def _get_compile_cpp_workflow(self) -> Workflow:
        """
        Creates a workflow that compiles a cpp file.
        Used templates:
        - <FILE> -- a path to the cpp file.
        - <OUT> -- a path to the output file.
        """
        wf = Workflow(
            "Compile cpp file",
        )

        # Create objects
        file_obj = wf.objects_manager.get_or_create_object("<FILE>")
        compiled_obj = wf.objects_manager.get_or_create_object("<OUT>")

        compiler = self.package.get_cpp_compiler_full_name()
        compiler_path = self.package.get_cpp_compiler_path()
        exec_compiler = ExecutionTask(
            f"Compile <FILE> using {compiler}",
            wf,
            exclusive=False,
            hard_time_limit=constants.COMPILERS_CPP_HARD_TIME_LIMIT,
            output_register="obsreg:compilation_result",
        )
        default_rg = ResourceGroup()
        exec_compiler.add_resource_group(default_rg)

        # Create filesystems
        file_fs = ObjectFilesystem(file_obj)
        exec_compiler.add_filesystem(file_fs)
        file_mp = Mountpoint(
            source=file_fs,
            target="/file.cpp",
        )
        compilation_ms = MountNamespace(
            mountpoints=[file_mp],
        )
        exec_compiler.add_mount_namespace(compilation_ms)
        compiler_proc = Process(
            wf,
            exec_compiler,
            image=f"compiler:{compiler}",
            arguments=[compiler_path, "/file.cpp", "-o", "/<OUT>"] + self.package.get_cpp_compiler_flags(),
            mount_namespace=compilation_ms,
            resource_group=default_rg,
            working_directory="/",
        )

        # TODO: Fix this. this should not be a stream as fd
        out_stream = ObjectWriteStream(compiled_obj)
        compiler_proc.descriptor_manager.add(2137, out_stream)

        exec_compiler.add_process(compiler_proc)
        wf.add_task(exec_compiler)
        return wf

    def _get_compile_python_workflow(self) -> Workflow:
        """
        Creates a workflow that compiles a python file.
        We'll probably have a special script that adds shebang
        and makes the file executable.
        Used templates:
        - <FILE> -- a path to the python file.
        - <OUT> -- a path to the output file.
        """
        wf = Workflow(
            "Compile python file",
        )

        # Create objects
        file_obj = wf.objects_manager.get_or_create_object("<FILE>")
        compiled_obj = wf.objects_manager.get_or_create_object("<OUT>")

        # Create execution task
        compiler = self.package.get_python_compiler_full_name()
        compiler_path = self.package.get_python_compiler_path()
        exec_compiler = ExecutionTask(
            f"Compile <FILE> using {compiler}",
            wf,
            exclusive=False,
            hard_time_limit=constants.COMPILERS_PYTHON_HARD_TIME_LIMIT,
            output_register="obsreg:compilation_result",
        )
        default_rg = ResourceGroup()
        exec_compiler.add_resource_group(default_rg)

        # Create filesystems
        file_fs = ObjectFilesystem(file_obj)
        exec_compiler.add_filesystem(file_fs)
        file_mp = Mountpoint(
            source=file_fs,
            target="/file.py",
        )
        compilation_ms = MountNamespace(
            mountpoints=[file_mp],
        )
        exec_compiler.add_mount_namespace(compilation_ms)

        compiler_proc = Process(
            wf,
            exec_compiler,
            image=f"python:{compiler}",
            arguments=[compiler_path, "/file.py", "-o", "/<OUT>"],
            mount_namespace=compilation_ms,
            resource_group=default_rg,
            working_directory="/",
        )

        # TODO: Fix this. this should not be a stream as fd
        out_stream = ObjectWriteStream(compiled_obj)
        compiler_proc.descriptor_manager.add(2137, out_stream)

        exec_compiler.add_process(compiler_proc)
        wf.add_task(exec_compiler)

        return wf

    def _get_compile_files_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Creates workflows for compiling required files, like checkers.
        """
        raise NotImplementedError

    def _get_generate_tests_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Creates workflows for generating tests.
        """
        raise NotImplementedError

    def _get_verify_workflows(self, data: dict) -> tuple[Workflow, bool]:
        raise NotImplementedError

    def _get_unpack_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Get all workflows that are used to unpack the given data.
        """
        if self._unpack_stage == UnpackStage.COMPILE_FILES:
            workflow, last = self._get_compile_files_workflows(data)
            if last:
                if self._has_test_gen:
                    self._unpack_stage = UnpackStage.GEN_TESTS
                elif self._has_verify:
                    self._unpack_stage = UnpackStage.VERIFY
                else:
                    self._unpack_stage = UnpackStage.FINISHED
        elif self._unpack_stage == UnpackStage.GEN_TESTS:
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

    def get_unpack_operation(
        self, has_test_gen: bool, has_verify: bool, return_func: callable = None
    ) -> WorkflowOperation:
        self._has_test_gen = has_test_gen
        self._has_verify = has_verify
        # At first, compile all required files
        self._unpack_stage = UnpackStage.COMPILE_FILES
        return WorkflowOperation(
            self._get_unpack_workflows, return_results=(return_func is not None), return_results_func=return_func
        )

    def get_run_operation(
        self, program: File, tests: list[Test] | None = None, return_func: callable = None
    ) -> WorkflowOperation:
        raise NotImplementedError

    def get_user_out_operation(self, program: File, test: Test, return_func: callable = None) -> WorkflowOperation:
        raise NotImplementedError

    def get_test_run_operation(self, program: File, test: File, return_func: callable = None) -> WorkflowOperation:
        raise NotImplementedError
