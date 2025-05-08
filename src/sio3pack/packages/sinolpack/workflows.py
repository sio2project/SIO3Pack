import os
from enum import Enum
from typing import Any, Tuple

from sio3pack import lua
from sio3pack.exceptions import WorkflowCreationError
from sio3pack.files import File
from sio3pack.packages.sinolpack import constants
from sio3pack.test import Test
from sio3pack.workflow import ExecutionTask, ScriptTask, Workflow, WorkflowManager, WorkflowOperation
from sio3pack.workflow.execution import MountNamespace, ObjectReadStream, ObjectWriteStream, Process, ResourceGroup
from sio3pack.workflow.execution.filesystems import EmptyFilesystem, ImageFilesystem, ObjectFilesystem
from sio3pack.workflow.execution.mount_namespace import Mountpoint


class UnpackStage(Enum):
    NONE = 0
    INGEN = 1
    OUTGEN = 2
    INWER = 3
    FINISHED = 4


class SinolpackWorkflowManager(WorkflowManager):
    def __init__(self, package: "Sinolpack", workflows: dict[str, Any]):
        super().__init__(package, workflows)
        self._has_ingen = False
        self._has_outgen = False
        self._has_inwer = False
        self._sp_unpack_stage = UnpackStage.NONE

    def get_compile_file_workflow(self, file: File | str) -> tuple[Workflow, str]:
        """
        Creates a workflow that compiles the given file and returns the path to the compiled file.
        The difference between this function and the base class is that this function
        adds the `extra_compilation_files` to the workflow.
        """
        wf, exe_path = super().get_compile_file_workflow(file)
        for task in wf.tasks:
            if isinstance(task, ExecutionTask):
                for extra_file in self.package.get_extra_compilation_files():
                    extra_obj = wf.objects_manager.get_or_create_object(extra_file.path)
                    wf.add_external_object(extra_obj)
                    extra_fs = ObjectFilesystem(extra_obj)
                    task.add_filesystem(extra_fs)
                    extra_mp = Mountpoint(
                        source=extra_fs,
                        target=f"/{extra_file.filename}",
                    )
                    task.processes[0].mount_namespace.add_mountpoint(extra_mp)
        return wf, exe_path

    def _get_ingen_workflow(self) -> Workflow:
        workflow = Workflow(
            "ingen",
            observable_registers=1,
        )
        ingen_path = self.package.get_ingen_path()
        if not ingen_path:
            raise WorkflowCreationError("Creating ingen workflow when no ingen present")

        ingen = workflow.objects_manager.get_or_create_object(ingen_path)
        workflow.add_external_object(ingen)

        # Compile ingen
        compile_wf, ingen_exe_path = self.get_compile_file_workflow(ingen_path)
        ingen_exe_obj = workflow.objects_manager.get_or_create_object(ingen_exe_path)
        workflow.union(compile_wf)

        # Run ingen
        exec_ingen = ExecutionTask(
            "Run ingen",
            workflow,
            exclusive=False,
            hard_time_limit=constants.INGEN_HARD_TIME_LIMIT,
            output_register=1,
        )
        default_rg = ResourceGroup()
        exec_ingen.resource_group_manager.add(default_rg)

        ingen_fs = ObjectFilesystem(
            object=ingen_exe_obj,
        )
        exec_ingen.add_filesystem(ingen_fs)
        ingen_mp = Mountpoint(
            source=ingen_fs,
            target="/ingen",
        )

        indir_fs = EmptyFilesystem()
        exec_ingen.add_filesystem(indir_fs)
        indir_mp = Mountpoint(
            source=indir_fs,
            target="/inputs",
            writable=True,
            capacity=constants.INGEN_MAX_INPUTS_SIZE,
        )

        ingen_ms = MountNamespace(
            mountpoints=[ingen_mp, indir_mp],
        )
        exec_ingen.add_mount_namespace(ingen_ms)
        ingen_proc = Process(
            workflow,
            exec_ingen,
            arguments=["/ingen"],
            mount_namespace=ingen_ms,
            resource_group=default_rg,
            working_directory="/inputs",
        )
        exec_ingen.add_process(ingen_proc)
        workflow.add_task(exec_ingen)

        return workflow

    def _get_outgen_test_workflow(self) -> Workflow:
        """
        Creates a workflow that runs outgen for a test. It is assumed,
        that the register `r:outgen_res_<TEST_ID>` has the execution info of outgen.
        Used templates:
        - <IN_TEST_PATH>
        - <OUT_TEST_PATH>
        - <TEST_ID>
        - <COMPILED_OUTGEN_PATH> -- a path to the compiled outgen file.
        """
        workflow = Workflow(
            "Generate output test for <TEST_ID>",
        )

        # Create objects for outgen and tests
        outgen_obj = workflow.objects_manager.get_or_create_object("<COMPILED_OUTGEN_PATH>")
        in_test_obj = workflow.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        out_test_obj = workflow.objects_manager.get_or_create_object("<OUT_TEST_PATH>")

        # Run the outgen, on stdin it will get the input test object and stdout is
        # piped to the output test object.
        exec_outgen = ExecutionTask(
            "Run outgen on test <TEST_ID>",
            workflow,
            exclusive=False,
            hard_time_limit=constants.OUTGEN_HARD_TIME_LIMIT,
            output_register="r:outgen_res_<TEST_ID>",
        )
        default_rg = ResourceGroup()
        exec_outgen.resource_group_manager.add(default_rg)
        outgen_fs = ObjectFilesystem(
            object=outgen_obj,
        )
        exec_outgen.add_filesystem(outgen_fs)
        outgen_mp = Mountpoint(
            source=outgen_fs,
            target="/outgen",
        )

        outgen_ms = MountNamespace(
            mountpoints=[outgen_mp],
        )
        exec_outgen.add_mount_namespace(outgen_ms)
        outgen_proc = Process(
            workflow,
            exec_outgen,
            arguments=["/outgen"],
            mount_namespace=outgen_ms,
            resource_group=default_rg,
            working_directory="/",
        )

        # Link stdin and stdout to the test objects
        in_stream = ObjectReadStream(in_test_obj)
        out_stream = ObjectWriteStream(out_test_obj)
        outgen_proc.descriptor_manager.add(0, in_stream)
        outgen_proc.descriptor_manager.add(1, out_stream)

        # Add the process to the task
        exec_outgen.add_process(outgen_proc)
        workflow.add_task(exec_outgen)
        return workflow

    def _get_verify_outgen_workflow(self) -> Workflow:
        """
        Creates a workflow that verifies if outgen was successful.
        The default implementation has only one script task, which checks
        if all outgens finished successfully.
        Used templates:
        - <LUA_MAP_TEST_ID_REG> -- a template for LUA scripts, that has
          a mapping of test IDs to registers.
        - <INPUT_REGS> -- a list of input registers, that are used to check
          if the outgen was successful.
        """
        workflow = Workflow(
            "Verify outgen",
        )
        script = ScriptTask(
            "Verify outgen",
            workflow,
            reactive=False,
            input_registers=["<INPUT_REGS>"],
            output_registers=["obsreg:result"],
            script=lua.get_script("verify_outgen"),
        )
        workflow.add_task(script)
        return workflow

    def get_default(self, name: str) -> Workflow:
        wf = super().get_default(name)
        if wf is not None:
            return wf
        if name == "ingen":
            return self._get_ingen_workflow()
        elif name == "outgen_test":
            return self._get_outgen_test_workflow()
        elif name == "verify_outgen":
            return self._get_verify_outgen_workflow()
        elif name == "inwer":
            return self._get_inwer_test_workflow()
        elif name == "verify_inwer":
            return self._get_verify_inwer_workflow()
        elif name == "run_test":
            return self._get_run_test_workflow()
        elif name == "grade_group":
            return self._get_grade_group_workflow()
        elif name == "grade_run":
            return self._get_grade_run_workflow()
        elif name == "user_out":
            return self._get_default_user_out_workflow()
        elif name == "test_run":
            return self._get_default_test_run_workflow()
        else:
            raise NotImplementedError(f"Default workflow for {name} not implemented.")

    def _get_compile_files_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Creates a workflow that compiles the checker, if it exists.
        """
        checker = self.package.get_checker_file()
        if checker is None:
            wf = Workflow("Nothing to compile")
            return wf, True

        wf = Workflow("Compile checker")
        checker_obj = wf.objects_manager.get_or_create_object(checker.path)
        wf.add_external_object(checker_obj)
        compile_wf, exe_path = self.get_compile_file_workflow(checker)
        exe_obj = wf.objects_manager.get_or_create_object(exe_path)
        wf.add_observable_object(exe_obj)
        wf.union(compile_wf)
        return wf, True

    def _get_generate_tests_workflows(self, data: dict) -> tuple[Workflow, bool]:
        if self._sp_unpack_stage == UnpackStage.INGEN:
            workflow = self.get("ingen")
            last = False
            if self._has_outgen:
                self._sp_unpack_stage = UnpackStage.OUTGEN
            elif self._has_inwer:
                self._sp_unpack_stage = UnpackStage.INWER
            else:
                last = True
            return workflow, last
        elif self._sp_unpack_stage == UnpackStage.OUTGEN:
            data = data or {}
            tests_with_inputs = self.package.get_tests_with_inputs()

            # List of filenames of input tests that were either generated by ingen or already present in the package.
            input_tests = set(data.get("input_tests", [])).union(set([t.in_file.path for t in tests_with_inputs]))

            workflow = Workflow("Outgen tests", observable_registers=1)

            # Compile outgen
            outgen_path = self.package.get_outgen_path()
            if not outgen_path:
                raise WorkflowCreationError("Creating outgen workflow when no model solution present")
            outgen_obj = workflow.objects_manager.get_or_create_object(outgen_path)
            workflow.add_external_object(outgen_obj)
            compile_wf, outgen_exe_path = self.get_compile_file_workflow(outgen_path)
            workflow.objects_manager.get_or_create_object(outgen_exe_path)
            workflow.union(compile_wf)

            outgen_output_registers = {}
            script_input_regs = []
            for in_test in input_tests:
                test_id = self.package.get_test_id_from_filename(os.path.basename(in_test))
                out_test = self.package.get_corresponding_out_filename(os.path.basename(in_test))
                in_test_obj = workflow.objects_manager.get_or_create_object(in_test)
                out_test_obj = workflow.objects_manager.get_or_create_object(out_test)
                workflow.add_external_object(in_test_obj)
                workflow.add_observable_object(out_test_obj)

                outgen_test_wf = self.get("outgen_test")
                outgen_test_wf.replace_templates(
                    {
                        "<IN_TEST_PATH>": in_test,
                        "<OUT_TEST_PATH>": out_test,
                        "<TEST_ID>": test_id,
                        "<COMPILED_OUTGEN_PATH>": outgen_exe_path,
                    }
                )
                script_input_regs.append(f"r:outgen_res_{test_id}")
                outgen_output_registers[test_id] = f"<r:outgen_res_{test_id}>"
                workflow.union(outgen_test_wf)

            # Now, get a workflow that checks if all outgens successfully finished.
            verify_wf = self.get("verify_outgen")
            verify_wf.replace_templates(
                {
                    "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(outgen_output_registers),
                    "<INPUT_REGS>": script_input_regs,
                }
            )
            workflow.union(verify_wf)
            return workflow, True

    def _get_inwer_test_workflow(self) -> Workflow:
        """
        Creates a workflow that runs inwer for a test. It is assumed,
        that the register `r:inwer_res_<TEST_ID>` has the execution info of inwer.
        Used templates:
        - <IN_TEST_PATH>
        - <TEST_ID>
        - <COMPILED_INWER_PATH> -- a path to the compiled inwer file.
        """
        workflow = Workflow(
            "Inwer for test",
        )

        # Create objects for inwer and input test
        inwer_obj = workflow.objects_manager.get_or_create_object("<COMPILED_INWER_PATH>")
        in_test_obj = workflow.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        workflow.add_external_object(in_test_obj)

        # Run the inwer, on stdin it will get the input test object and test ID
        # as an argument.
        exec_inwer = ExecutionTask(
            "Run inwer on test <TEST_ID>",
            workflow,
            exclusive=False,
            hard_time_limit=constants.INWER_HARD_TIME_LIMIT,
            output_register="r:inwer_res_<TEST_ID>",
        )
        default_rg = ResourceGroup()
        exec_inwer.resource_group_manager.add(default_rg)
        inwer_fs = ObjectFilesystem(
            object=inwer_obj,
        )
        exec_inwer.add_filesystem(inwer_fs)
        inwer_mp = Mountpoint(
            source=inwer_fs,
            target="/inwer",
        )

        inwer_ms = MountNamespace(
            mountpoints=[inwer_mp],
        )
        exec_inwer.add_mount_namespace(inwer_ms)
        inwer_proc = Process(
            workflow,
            exec_inwer,
            arguments=["/inwer", "<TEST_ID>"],
            mount_namespace=inwer_ms,
            resource_group=default_rg,
            working_directory="/",
        )

        # Link stdin to the test object
        in_stream = ObjectReadStream(in_test_obj)
        inwer_proc.descriptor_manager.add(0, in_stream)

        # Add the process to the task
        exec_inwer.add_process(inwer_proc)
        workflow.add_task(exec_inwer)
        return workflow

    def _get_verify_inwer_workflow(self) -> Workflow:
        """
        Creates a workflow that verifies if inwer was successful.
        The default implementation has only one script task, which checks
        if all inwers finished successfully.
        Used templates:
        - <LUA_MAP_TEST_ID_REG> -- a template for LUA scripts, that has
          a mapping of test IDs to registers.
        - <INPUT_REGS> -- a list of input registers, that are used to check
          if the outgen was successful.
        """
        workflow = Workflow(
            "Verify inwer",
        )
        script = ScriptTask(
            "Verify inwer",
            workflow,
            reactive=False,
            input_registers=["<INPUT_REGS>"],
            output_registers=["obsreg:result"],
            script=lua.get_script("verify_inwer"),
        )
        workflow.add_task(script)
        return workflow

    def _get_verify_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Creates a workflow that runs inwer.
        """
        input_tests: list["Test"] = self.package.get_input_tests()
        workflow = Workflow("Inwer", observable_registers=1)

        # Compile inwer
        inwer_path = self.package.get_inwer_path()
        if not inwer_path:
            raise WorkflowCreationError("Creating inwer workflow when no inwer present")
        inwer_obj = workflow.objects_manager.get_or_create_object(inwer_path)
        workflow.add_external_object(inwer_obj)
        compile_wf, inwer_exe_path = self.get_compile_file_workflow(inwer_path)
        workflow.objects_manager.get_or_create_object(inwer_exe_path)
        workflow.union(compile_wf)

        inwer_output_registers = {}
        script_input_regs = []
        for test in input_tests:
            test_id = test.test_id
            inwer_test_wf = self.get("inwer")
            inwer_test_wf.replace_templates(
                {
                    "<IN_TEST_PATH>": test.in_file.path,
                    "<TEST_ID>": test_id,
                    "<COMPILED_INWER_PATH>": inwer_exe_path,
                }
            )
            script_input_regs.append(f"r:inwer_res_{test_id}")
            inwer_output_registers[test_id] = f"<r:inwer_res_{test_id}>"
            workflow.union(inwer_test_wf)

        # Now, get a workflow that checks if all inwer successfully finished.
        verify_wf = self.get("verify_inwer")
        verify_wf.replace_templates(
            {
                "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(inwer_output_registers),
                "<INPUT_REGS>": script_input_regs,
            }
        )
        workflow.union(verify_wf)
        return workflow, True

    def get_unpack_operation(
        self, has_ingen: bool, has_outgen: bool, has_inwer: bool, return_func: callable = None
    ) -> WorkflowOperation:
        """
        Get the unpack operation for the given data.
        """
        self._has_ingen = has_ingen
        self._has_outgen = has_outgen
        self._has_inwer = has_inwer
        if self._has_ingen:
            self._sp_unpack_stage = UnpackStage.INGEN
        elif self._has_outgen:
            self._sp_unpack_stage = UnpackStage.OUTGEN
        elif self._has_inwer:
            self._sp_unpack_stage = UnpackStage.INWER
        else:
            # This will be handled by the base class, since there is no unpacking to do.
            pass
        return super().get_unpack_operation(
            has_test_gen=(has_ingen or has_outgen), has_verify=has_inwer, return_func=return_func
        )

    def _add_extra_execution_files(self, workflow: Workflow, task: ExecutionTask) -> list[Mountpoint]:
        """
        Adds extra execution files from config file to the task.

        :param workflow: The workflow to add the extra execution files to.
        :param task: The task to add the extra execution files to.
        :return: A list of mountpoints for the extra execution files.
        """
        mps = []
        for file in self.package.get_extra_execution_files():
            file_obj = workflow.objects_manager.get_or_create_object(file.path)
            workflow.add_external_object(file_obj)
            file_fs = ObjectFilesystem(file_obj)
            task.add_filesystem(file_fs)
            file_mp = Mountpoint(
                source=file_fs,
                target=f"/{file.filename}",
            )
            mps.append(file_mp)
        return mps

    def _get_run_test_workflow(self) -> Workflow:
        """
        Creates a workflow that runs the solution for a test and verifies the output with the checker.
        Used templates:
        - <TEST_ID>
        - <IN_TEST_PATH>
        - <OUT_TEST_PATH>
        - <SOL_PATH>
        """
        wf = Workflow(
            name="Run test",
        )
        in_test_obj = wf.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        out_test_obj = wf.objects_manager.get_or_create_object("<OUT_TEST_PATH>")
        sol_obj = wf.objects_manager.get_or_create_object("<SOL_PATH>")
        wf.add_external_object(in_test_obj)
        wf.add_external_object(out_test_obj)

        # This object will store the output of the solution.
        user_out_obj = wf.objects_manager.get_or_create_object("user_out_<TEST_ID>")

        # Run the solution, on stdin it will get the input test object and stdout is
        # piped to a new object which is user out. The name is important, because
        # the resource group in the task beginning with the "Run solution for test" will
        # be set with correct time limit and memory limit.
        exec_run = ExecutionTask(
            "Run solution for test <TEST_ID>",
            wf,
            exclusive=False,
            output_register="r:run_test_res_<TEST_ID>",
        )
        rg = ResourceGroup()
        exec_run.resource_group_manager.add(rg)
        run_fs = ObjectFilesystem(
            object=sol_obj,
        )
        exec_run.add_filesystem(run_fs)
        run_mp = Mountpoint(
            source=run_fs,
            target="/exe",
        )

        extra_mps = self._add_extra_execution_files(wf, exec_run)
        run_ms = MountNamespace(
            mountpoints=[run_mp] + extra_mps,
        )
        exec_run.add_mount_namespace(run_ms)
        run_proc = Process(
            wf,
            exec_run,
            arguments=["/exe"],
            mount_namespace=run_ms,
            resource_group=rg,
            working_directory="/",
        )

        # Link stdin to input test object and stdout to user out object
        in_stream = ObjectReadStream(in_test_obj)
        out_stream = ObjectWriteStream(user_out_obj)
        run_proc.descriptor_manager.add(0, in_stream)
        run_proc.descriptor_manager.add(1, out_stream)

        # Add the process to the task
        exec_run.add_process(run_proc)
        wf.add_task(exec_run)

        # Now, run the checker. It will be run with input test, output test and user out as execution arguments.
        # If there is no custom checker, use the default oicompare image.
        exec_chk = ExecutionTask(
            "Run checker for test <TEST_ID>",
            wf,
            exclusive=False,
            hard_time_limit=constants.CHECKER_HARD_TIME_LIMIT,
            output_register="r:checker_res_<TEST_ID>",
        )
        rg = ResourceGroup()
        exec_chk.resource_group_manager.add(rg)

        checker_path = self.package.get_checker_path()
        if checker_path is None:
            chk_fs = ImageFilesystem("checkers:oicompare")
        else:
            exe_checker = self.package.get_executable_path(checker_path)
            checker_obj = wf.objects_manager.get_or_create_object(exe_checker)
            chk_fs = ObjectFilesystem(
                object=checker_obj,
            )
        exec_chk.add_filesystem(chk_fs)
        chk_mp = Mountpoint(
            source=chk_fs,
            target="/chk",
        )
        in_fs = ObjectFilesystem(in_test_obj)
        exec_chk.add_filesystem(in_fs)
        in_mp = Mountpoint(
            source=in_fs,
            target="/in",
        )
        out_fs = ObjectFilesystem(out_test_obj)
        exec_chk.add_filesystem(out_fs)
        out_mp = Mountpoint(
            source=out_fs,
            target="/out",
        )
        user_out_fs = ObjectFilesystem(user_out_obj)
        exec_chk.add_filesystem(user_out_fs)
        user_out_mp = Mountpoint(
            source=user_out_fs,
            target="/user_out",
        )

        chk_ms = MountNamespace(
            mountpoints=[chk_mp, in_mp, out_mp, user_out_mp],
        )
        exec_chk.add_mount_namespace(chk_ms)
        chk_proc = Process(
            wf,
            exec_chk,
            arguments=["/chk", "/in", "/out", "/user_out"],
            mount_namespace=chk_ms,
            resource_group=rg,
            working_directory="/",
        )

        # Link stdout of the checker to an object stream.
        chk_out_obj = wf.objects_manager.get_or_create_object("chk_out_<TEST_ID>")
        chk_out_stream = ObjectWriteStream(chk_out_obj)
        chk_proc.descriptor_manager.add(1, chk_out_stream)

        # Add the process to the task
        exec_chk.add_process(chk_proc)
        wf.add_task(exec_chk)

        # At the end, grade the test by checking checker output, return code and
        # user's program status. The script is reactive, because for example when
        # the solution gets Runtime Error, we don't have to check checker output.
        grade = ScriptTask(
            "Grade test <TEST_ID>",
            wf,
            reactive=True,
            input_registers=["r:run_test_res_<TEST_ID>", "r:checker_res_<TEST_ID>"],
            output_registers=["r:grade_res_<TEST_ID>"],
            objects=[chk_out_obj],
            script=lua.get_script("grade_test"),
        )
        wf.add_task(grade)
        return wf

    def _get_grade_group_workflow(self) -> Workflow:
        """
        Creates a workflow that grades the group of tests. The script is
        reactive, because it's possible that we can exit the grading
        process early.
        Used templates:
        - <LUA_MAP_TEST_ID_REG> -- a template for LUA scripts, that has
          a mapping of test IDs to registers.
        - <INPUT_REGS> -- a list of input registers, that have grading
          results of the tests.
        - <GROUP_ID> -- a group ID of the tests.
        """
        workflow = Workflow(
            name="Grade group",
        )
        script = ScriptTask(
            "Grade group <GROUP_ID>",
            workflow,
            reactive=True,
            input_registers=["<INPUT_REGS>"],
            output_registers=["r:group_grade_res_<GROUP_ID>"],
            script=lua.get_script("grade_group"),
        )
        workflow.add_task(script)
        return workflow

    def _get_grade_run_workflow(self) -> Workflow:
        """
        Creates a workflow that grades the run of the solution. The script is
        reactive, because it's possible that we can exit the grading
        process early.
        Used templates:
        - <LUA_MAP_TEST_ID_REG> -- a template for LUA scripts, that has
          a mapping of group IDs to registers.
        - <INPUT_REGS> -- a list of input registers, that have grading
          results of the groups.
        """
        workflow = Workflow(
            name="Grade run",
        )
        script = ScriptTask(
            "Grade run",
            workflow,
            reactive=True,
            input_registers=["<INPUT_REGS>"],
            output_registers=["obsreg:result"],
            script=lua.get_script("grade_run"),
        )
        workflow.add_task(script)
        return workflow

    def _get_run_workflow(self, data: dict, program: File, tests: list[Test] | None = None) -> Tuple[Workflow, bool]:
        if tests is None:
            tests = self.package.tests

        workflow = Workflow(
            name="Run solution",
        )
        language = self.package.get_file_language(program)

        # Compile the solution
        program_obj = workflow.objects_manager.get_or_create_object(program.path)
        workflow.add_external_object(program_obj)
        compile_wf, exe_path = self.get_compile_file_workflow(program)
        workflow.objects_manager.get_or_create_object(exe_path)
        workflow.union(compile_wf)

        groups = {}
        for test in tests:
            if test.group not in groups:
                groups[test.group] = []
            groups[test.group].append(test)
            workflow.add_external_object(workflow.objects_manager.get_or_create_object(test.in_file.path))
            workflow.add_external_object(workflow.objects_manager.get_or_create_object(test.out_file.path))

        checker_path = self.package.get_checker_path()
        if checker_path is not None:
            checker_exe_path = self.package.get_executable_path(checker_path)
            checker_obj = workflow.objects_manager.get_or_create_object(checker_exe_path)
            workflow.add_external_object(checker_obj)

        output_registers = []
        output_registers_map = {}
        for group, tests in groups.items():
            group_out_registers = []
            group_out_registers_map = {}

            # Run the solution for each test in the group and grade it.
            for test in tests:
                test_id = test.test_id
                run_test_wf = self.get("run_test")
                group_out_registers.append(f"r:grade_res_{test_id}")
                group_out_registers_map[test_id] = f"<r:grade_res_{test_id}>"
                run_test_wf.replace_templates(
                    {
                        "<IN_TEST_PATH>": test.in_file.path,
                        "<OUT_TEST_PATH>": test.out_file.path,
                        "<SOL_PATH>": exe_path,
                        "<TEST_ID>": test_id,
                    }
                )

                # Find the task which executes the solution and fix the resource group
                time_limit = self.package.get_time_limit_for_test(test, language)
                memory_limit = self.package.get_memory_limit_for_test(test, language)
                for task in run_test_wf.tasks:
                    if isinstance(task, ExecutionTask) and task.name == f"Run solution for test {test_id}":
                        for process in task.processes:
                            process.resource_group.set_limits(100, time_limit * 1e9, memory_limit, time_limit)

                workflow.union(run_test_wf)

            # Now, run the grading script for the group.
            grade_group_wf = self.get("grade_group")
            grade_group_wf.replace_templates(
                {
                    "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(group_out_registers_map),
                    "<INPUT_REGS>": group_out_registers,
                    "<GROUP_ID>": group,
                }
            )
            workflow.union(grade_group_wf)
            output_registers.append(f"r:group_grade_res_{group}")
            output_registers_map[group] = f"<r:group_grade_res_{group}>"

        # Finally, add the script that grades the whole solution.
        grade_run_wf = self.get("grade_run")
        grade_run_wf.replace_templates(
            {
                "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(output_registers_map),
                "<INPUT_REGS>": output_registers,
            }
        )
        workflow.union(grade_run_wf)
        return workflow, True

    def get_run_operation(
        self, program: File, tests: list[Test] | None = None, return_func: callable = None
    ) -> WorkflowOperation:
        """
        Get the run operation for the given data.
        """
        return WorkflowOperation(
            self._get_run_workflow,
            return_results=(return_func is not None),
            return_results_func=return_func,
            program=program,
            tests=tests,
        )

    def _get_default_user_out_workflow(self) -> Workflow:
        """
        Creates a workflow that generates the user output for a test.
        Used templates:
        - <TEST_ID> -- a test ID of the test.
        - <IN_TEST_PATH> -- a path to the input test file.
        - <SOL_PATH> -- a path to the solution file.
        """
        wf = Workflow(
            name="Generate user out",
        )
        in_test_obj = wf.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        sol_obj = wf.objects_manager.get_or_create_object("<SOL_PATH>")
        out_obj = wf.objects_manager.get_or_create_object("user_out_<TEST_ID>")
        wf.add_external_object(in_test_obj)

        wf.add_observable_object(out_obj)

        # Run the solution, on stdin it will get the input test object and stdout is
        # piped to a new object which is user out.
        exec_run = ExecutionTask(
            "Run solution for test <TEST_ID>",
            wf,
            exclusive=False,
            output_register="obsreg:result",
        )
        rg = ResourceGroup()
        exec_run.resource_group_manager.add(rg)
        run_fs = ObjectFilesystem(
            object=sol_obj,
        )
        exec_run.add_filesystem(run_fs)
        run_mp = Mountpoint(
            source=run_fs,
            target="/exe",
        )
        extra_mps = self._add_extra_execution_files(wf, exec_run)
        run_ms = MountNamespace(
            mountpoints=[run_mp] + extra_mps,
        )
        exec_run.add_mount_namespace(run_ms)
        run_proc = Process(
            wf,
            exec_run,
            arguments=["/exe"],
            mount_namespace=run_ms,
            resource_group=rg,
            working_directory="/",
        )

        # Link stdin to input test object and stdout to user out object
        in_stream = ObjectReadStream(in_test_obj)
        out_stream = ObjectWriteStream(out_obj)
        run_proc.descriptor_manager.add(0, in_stream)
        run_proc.descriptor_manager.add(1, out_stream)

        # Add the process to the task
        exec_run.add_process(run_proc)
        wf.add_task(exec_run)
        return wf

    def _get_user_out_workflow(self, data: dict, program: File, test: Test) -> Tuple[Workflow, bool]:
        workflow = Workflow(
            name="Generate user out for test",
        )

        # Compile the solution
        program_obj = workflow.objects_manager.get_or_create_object(program.path)
        workflow.add_external_object(program_obj)
        compile_wf, exe_path = self.get_compile_file_workflow(program)
        workflow.objects_manager.get_or_create_object(exe_path)
        workflow.union(compile_wf)

        in_test_obj = workflow.objects_manager.get_or_create_object(test.in_file.path)
        user_out_obj = workflow.objects_manager.get_or_create_object(f"user_out_{test.test_id}")
        workflow.add_external_object(in_test_obj)
        workflow.add_observable_object(user_out_obj)

        user_out_wf = self.get("user_out")
        user_out_wf.replace_templates(
            {
                "<IN_TEST_PATH>": test.in_file.path,
                "<SOL_PATH>": exe_path,
                "<TEST_ID>": test.test_id,
            }
        )
        workflow.union(user_out_wf)
        return workflow, True

    def get_user_out_operation(self, program: File, test: Test, return_func: callable = None) -> WorkflowOperation:
        """
        Get the workflow for getting the user's output for a given test.
        """
        return WorkflowOperation(
            self._get_user_out_workflow,
            return_results=(return_func is not None),
            return_results_func=return_func,
            program=program,
            test=test,
        )

    def _get_default_test_run_workflow(self):
        """
        Creates a workflow that runs the given test on the given program.
        Used templates:
        - <IN_TEST_PATH> -- a path to the input test file.
        - <SOL_PATH> -- a path to the solution file.
        - <USER_OUT_PATH> -- a path to the user output file.
        """
        wf = Workflow(
            name="Test run",
        )
        in_test_obj = wf.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        sol_obj = wf.objects_manager.get_or_create_object("<SOL_PATH>")
        out_obj = wf.objects_manager.get_or_create_object("<USER_OUT_PATH>")
        wf.add_external_object(in_test_obj)

        wf.add_observable_object(out_obj)

        # Run the solution, on stdin it will get the input test object and stdout is
        # piped to a new object which is user out.
        exec_run = ExecutionTask(
            "Run solution for test",
            wf,
            exclusive=False,
            output_register="obsreg:result",
        )
        rg = ResourceGroup()
        exec_run.resource_group_manager.add(rg)
        run_fs = ObjectFilesystem(
            object=sol_obj,
        )
        exec_run.add_filesystem(run_fs)
        run_mp = Mountpoint(
            source=run_fs,
            target="/exe",
        )
        extra_mps = self._add_extra_execution_files(wf, exec_run)
        run_ms = MountNamespace(
            mountpoints=[run_mp] + extra_mps,
        )
        exec_run.add_mount_namespace(run_ms)
        run_proc = Process(
            wf,
            exec_run,
            arguments=["/exe"],
            mount_namespace=run_ms,
            resource_group=rg,
            working_directory="/",
        )

        # Link stdin to input test object and stdout to user out object
        in_stream = ObjectReadStream(in_test_obj)
        out_stream = ObjectWriteStream(out_obj)
        run_proc.descriptor_manager.add(0, in_stream)
        run_proc.descriptor_manager.add(1, out_stream)

        # Add the process to the task
        exec_run.add_process(run_proc)
        wf.add_task(exec_run)
        return wf

    def _get_test_run_workflow(self, data: dict, program: File, test: File) -> Tuple[Workflow, bool]:
        workflow = Workflow(
            name="Test run",
        )
        in_test_obj = workflow.objects_manager.get_or_create_object(test.path)
        user_out_obj = workflow.objects_manager.get_or_create_object(f"test_run_{program.filename}")
        workflow.add_external_object(in_test_obj)
        workflow.add_observable_object(user_out_obj)

        # Compile the solution
        program_obj = workflow.objects_manager.get_or_create_object(program.path)
        workflow.add_external_object(program_obj)
        compile_wf, exe_path = self.get_compile_file_workflow(program)
        workflow.objects_manager.get_or_create_object(exe_path)
        workflow.union(compile_wf)

        test_run_wf = self.get("test_run")
        test_run_wf.replace_templates(
            {
                "<IN_TEST_PATH>": test.path,
                "<SOL_PATH>": exe_path,
                "<USER_OUT_PATH>": user_out_obj.handle,
            }
        )
        workflow.union(test_run_wf)
        return workflow, True

    def get_test_run_operation(self, program: File, test: File, return_func: callable = None) -> WorkflowOperation:
        """
        Get the workflow for running a given test on a given program.
        """
        return WorkflowOperation(
            self._get_test_run_workflow,
            return_results=(return_func is not None),
            return_results_func=return_func,
            program=program,
            test=test,
        )
