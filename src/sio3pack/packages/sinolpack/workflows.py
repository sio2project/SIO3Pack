from enum import Enum

from sio3pack.exceptions import WorkflowCreationError
from sio3pack.packages.sinolpack import constants
from sio3pack.workflow import WorkflowManager, Workflow, WorkflowOperation, ExecutionTask
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

    def _get_outgen_test_workflow(self):
        """
        Creates a workflow that runs outgen for a test. It is assumed,
        that the zeroth register has the execution info of outgen.
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
        outgen_obj = workflow.objects_manager.get_or_create_object(outgen_path)
        in_test_obj = workflow.objects_manager.get_or_create_object("<IN_TEST_PATH>")
        out_test_obj = workflow.objects_manager.get_or_create_object("<OUT_TEST_PATH>")
        workflow.add_external_object(outgen_obj)

        exec_outgen = ExecutionTask(
            "Run outgen on test <TEST_ID>",
            workflow,
            exclusive=False,
            hard_time_limit=constants.OUTGEN_HARD_TIME_LIMIT,
            output_register=0,
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

        in_stream = ObjectReadStream(in_test_obj)
        out_stream = ObjectWriteStream(out_test_obj)
        outgen_proc.descriptor_manager.add(0, in_stream)
        outgen_proc.descriptor_manager.add(1, out_stream)
        exec_outgen.add_process(outgen_proc)
        workflow.add_task(exec_outgen)
        return workflow


    def get_default(self, name: str) -> Workflow:
        if name == "ingen":
            return self._get_ingen_workflow()
        elif name == "outgen_test":
            return self._get_outgen_test_workflow()
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
            input_tests = set(data["input_tests"]).union(set(self.package.get_input_tests()))
            workflow = Workflow("Outgen tests", observable_registers=1)
            outgen_output_registers = []
            for in_test in input_tests:
                out_test = self.package.get_corresponding_out_test(in_test)
                in_test_obj = workflow.objects_manager.get_or_create_object(in_test)
                out_test_obj = workflow.objects_manager.get_or_create_object(out_test)
                workflow.add_external_object(in_test_obj)
                workflow.add_observable_object(out_test_obj)

                outgen_test_wf = self.get("outgen_test")
                outgen_output_registers.append(workflow.get_num_registers())
                workflow.union(outgen_test_wf)


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
