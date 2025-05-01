import os

from enum import Enum

from sio3pack import lua
from sio3pack.exceptions import WorkflowCreationError
from sio3pack.packages.sinolpack import constants
from sio3pack.workflow import WorkflowManager, Workflow, WorkflowOperation, ExecutionTask, ScriptTask
from sio3pack.workflow.execution import Filesystem, MountNamespace, Process, ResourceGroup, ObjectStream, \
    ObjectReadStream, ObjectWriteStream
from sio3pack.workflow.execution.filesystems import ObjectFilesystem, EmptyFilesystem
from sio3pack.workflow.execution.mount_namespace import Mountpoint


class UnpackStage(Enum):
    NONE = 0
    INGEN = 1
    OUTGEN = 2
    INWER = 3
    FINISHED = 4


class SinolpackWorkflowManager(WorkflowManager):
    def __init__(self, package: "Sinolpack", workflows: dict[str, Workflow]):
        super().__init__(package, workflows)
        self._has_ingen = False
        self._has_outgen = False
        self._has_inwer = False
        self._sp_unpack_stage = UnpackStage.NONE

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
            object=ingen,
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
        """
        workflow = Workflow(
            "Generate output test for <TEST_ID>",
        )
        outgen_path = self.package.get_outgen_path()
        if not outgen_path:
            raise WorkflowCreationError("Creating outgen workflow when no outgen present")

        # Create objects for outgen and tests
        outgen_obj = workflow.objects_manager.get_or_create_object(outgen_path)
        in_test_obj = workflow.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        out_test_obj = workflow.objects_manager.get_or_create_object("<OUT_TEST_PATH>")
        workflow.add_external_object(outgen_obj)

        # Run the outgen, on stdin it will get the input test object and stdout is
        # piped to the output test object.
        exec_outgen = ExecutionTask(
            "Run outgen on test <TEST_ID>",
            workflow,
            exclusive=False,
            hard_time_limit=constants.OUTGEN_HARD_TIME_LIMIT,
            output_register='r:outgen_res_<TEST_ID>',
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
            script=lua.get_script("verify_outgen")
        )
        workflow.add_task(script)
        return workflow

    def get_default(self, name: str) -> Workflow:
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
        else:
            raise NotImplementedError(f"Default workflow for {name} not implemented.")

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
                outgen_test_wf.replace_templates({
                    "<IN_TEST_PATH>": in_test,
                    "<OUT_TEST_PATH>": out_test,
                    "<TEST_ID>": test_id,
                })
                script_input_regs.append(f'r:outgen_res_{test_id}')
                outgen_output_registers[test_id] = f'<r:outgen_res_{test_id}>'
                workflow.union(outgen_test_wf)

            # Now, get a workflow that checks if all outgens successfully finished.
            verify_wf = self.get("verify_outgen")
            verify_wf.replace_templates({
                "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(outgen_output_registers),
                "<INPUT_REGS>": script_input_regs,
            })
            workflow.union(verify_wf)
            return workflow, True

    def _get_inwer_test_workflow(self) -> Workflow:
        """
        Creates a workflow that runs inwer for a test. It is assumed,
        that the register `r:inwer_res_<TEST_ID>` has the execution info of inwer.
        Used templates:
        - <IN_TEST_PATH>
        - <TEST_ID>
        """
        workflow = Workflow(
            "Inwer for test",
        )
        inwer_path = self.package.get_inwer_path()
        if not inwer_path:
            raise WorkflowCreationError("Creating inwer workflow when no inwer present")

        # Create objects for inwer and input test
        inwer_obj = workflow.objects_manager.get_or_create_object(inwer_path)
        in_test_obj = workflow.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        workflow.add_external_object(inwer_obj)
        workflow.add_external_object(in_test_obj)

        # Run the inwer, on stdin it will get the input test object and test ID
        # as an argument.
        exec_inwer = ExecutionTask(
            "Run inwer on test <TEST_ID>",
            workflow,
            exclusive=False,
            hard_time_limit=constants.INWER_HARD_TIME_LIMIT,
            output_register='r:inwer_res_<TEST_ID>',
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
            script=lua.get_script("verify_inwer")
        )
        workflow.add_task(script)
        return workflow

    def _get_verify_workflows(self, data: dict) -> tuple[Workflow, bool]:
        """
        Creates a workflow that runs inwer.
        """
        data = data or {}
        input_tests: list["Test"] = self.package.get_input_tests()
        workflow = Workflow("Inwer", observable_registers=1)
        inwer_output_registers = {}
        script_input_regs = []
        for test in input_tests:
            test_id = test.test_id
            inwer_test_wf = self.get("inwer")
            inwer_test_wf.replace_templates({
                "<IN_TEST_PATH>": test.in_file.path,
                "<TEST_ID>": test_id,
            })
            script_input_regs.append(f'r:inwer_res_{test_id}')
            inwer_output_registers[test_id] = f'<r:inwer_res_{test_id}>'
            workflow.union(inwer_test_wf)

        # Now, get a workflow that checks if all inwer successfully finished.
        verify_wf = self.get("verify_inwer")
        verify_wf.replace_templates({
            "<LUA_MAP_TEST_ID_REG>": lua.to_lua_map(inwer_output_registers),
            "<INPUT_REGS>": script_input_regs,
        })
        workflow.union(verify_wf)
        return workflow, True

    def get_unpack_operation(self, has_ingen: bool, has_outgen: bool, has_inwer: bool, return_func: callable = None) -> WorkflowOperation:
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
        return super().get_unpack_operation(has_test_gen=(has_ingen or has_outgen), has_verify=has_inwer, return_func=return_func)
