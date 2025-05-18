import json
import os

import pytest
import yaml

import sio3pack
from sio3pack.exceptions import WorkflowCreationError
from sio3pack.packages import Sinolpack
from sio3pack.packages.package.configuration import SIO3PackConfig
from sio3pack.workflow import ExecutionTask, ScriptTask, Workflow
from sio3pack.workflow.execution import ObjectReadStream, ObjectWriteStream
from sio3pack.workflow.execution.filesystems import ObjectFilesystem
from tests.fixtures import PackageInfo, get_package
from tests.packages.sinolpack.utils import common_checks


def _get_run_types() -> list[str]:
    try:
        import django

        return ["file", "db"]
    except ImportError:
        return ["file"]


def _get_package(package_info: PackageInfo, type: str, config: SIO3PackConfig = None):
    config = config or SIO3PackConfig.detect()
    if type == "file":
        return sio3pack.from_file(package_info.path, config)
    elif type == "db":
        from sio3pack.django.common.models import SIO3Package

        package = sio3pack.from_file(package_info.path, config)
        id = SIO3Package.objects.all().count() + 1
        package.save_to_db(id)
        return sio3pack.from_db(id, config)


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple", "inwer"], indirect=True)
def test_unpack_workflows(get_package):
    for type in _get_run_types():
        print(f"From {type}")
        package_info: PackageInfo = get_package()
        package = _get_package(package_info, type)
        common_checks(package_info, package)

        op = package.get_unpack_operation()
        assert op is not None
        workflows = []
        for wf in op.get_workflow():
            workflows.append(wf)

        if package_info.task_id == "abc":
            # We expect 2 workflows: compile checker and outgen
            assert len(workflows) == 3
            assert workflows[0].name == "Compile files"
            assert workflows[1].name == "Run ingen"
            assert workflows[2].name == "Outgen tests"
        elif package_info.task_id == "wer":
            # We expect 3 workflows: compile checker, outgen and inwer
            assert len(workflows) == 3
            assert workflows[0].name == "Compile files"
            assert workflows[1].name == "Outgen tests"
            assert workflows[2].name == "Inwer"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["run"], indirect=True)
def test_run_workflow(get_package):
    for type in _get_run_types():
        print(f"From {type}")
        package_info: PackageInfo = get_package()
        package = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        op = package.get_run_operation(program)
        workflows = [wf for wf in op.get_workflow()]
        assert len(workflows) == 1

        assert workflows[0].name == "Run solution"
        compile_ok = False
        num_runs = 0
        num_runs_checker = 0
        num_grade_tests = 0
        num_grade_group = 0
        num_grade_all = 0
        for task in workflows[0].tasks:
            if isinstance(task, ExecutionTask):
                if task.name == f"Compile {program.path} using g++-12.2":
                    assert len(task.processes) == 1, "Compile task should have one process"
                    assert task.processes[0].image == "compiler:g++-12.2", "Compile task should use g++-12.2 image"
                    compile_ok = True
                elif task.name.startswith("Run solution for test"):
                    num_runs += 1
                    assert len(task.processes) == 1, "Run task should have one process"
                    proc = task.processes[0]
                    stdin_fd = proc.descriptor_manager.get(0)
                    assert isinstance(stdin_fd, ObjectReadStream), "Run task should have stdin stream"
                    stdout_fd = proc.descriptor_manager.get(1)
                    assert isinstance(stdout_fd, ObjectWriteStream), "Run task should have stdout stream"
                    assert stdout_fd.object.handle.startswith("user_out"), "Run task should have user_out stream"
                elif task.name.startswith("Run checker for test"):
                    num_runs_checker += 1
                    assert len(task.processes) == 1, "Checker task should have one process"
                    assert (
                        task.filesystem_manager.len() == 4
                    ), "Checker task should have 4 filesystems: checker, in, out and user_out"
                    proc = task.processes[0]
                    assert proc.descriptor_manager.size() == 1, "Checker task should have one descriptor"
                    stdout_fd = proc.descriptor_manager.get(1)
                    assert isinstance(stdout_fd, ObjectWriteStream), "Checker task should have stdout stream"
                else:
                    raise ValueError(f"Unknown task name: {task.name}")
            elif isinstance(task, ScriptTask):
                if task.name.startswith("Grade test"):
                    num_grade_tests += 1
                    assert (
                        len(task.input_registers) == 2
                    ), "Grade test task should have 2 input registers: checker result and user result"
                    assert len(task.objects) == 1, "Grade test task should have one object: user_out"
                    assert (
                        len(task.output_registers) == 1
                    ), "Grade test task should have one output register: grading result"
                elif task.name.startswith("Grade group"):
                    num_grade_group += 1
                    # In this task, there is only one test in each group
                    assert (
                        len(task.input_registers) == 1
                    ), "Grade group task should have one input register: grading result of the test"
                    assert (
                        len(task.output_registers) == 1
                    ), "Grade group task should have one output register: grading result"
                elif task.name == "Grade run":
                    num_grade_all += 1
                    assert (
                        len(task.input_registers) == 3
                    ), "Grade run task should have three input registers: grading result of the groups"
                    assert (
                        len(task.output_registers) == 1
                    ), "Grade run task should have one output register: grading result"
                else:
                    raise ValueError(f"Unknown task name: {task.name}")
            else:
                raise ValueError(f"Unknown task type: {type(task)}")

        assert compile_ok, "Compile task should be ok"
        assert num_runs == num_runs_checker == num_grade_tests == 3, "Should have 3 runs"
        assert num_grade_group == 3, "Should have 3 groups"
        assert num_grade_all == 1, "Should have one grade run"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["custom_workflows"], indirect=True)
def test_custom_workflow(get_package):
    for type in _get_run_types():
        package_info: PackageInfo = get_package()
        package = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        op = package.get_run_operation(program)
        workflows = [wf for wf in op.get_workflow()]
        assert len(workflows) == 1

        assert workflows[0].name == "Run solution"
        workflow: Workflow = workflows[0]

        num_custom = 0
        num_custom_scripts = 0
        for task in workflow.tasks:
            if task.name == "Run test two times":
                assert isinstance(task, ExecutionTask), "Custom task should be an execution task"
                num_custom += 1
                assert len(task.processes) == 2, "Custom task should have two processes"
                stream1 = task.processes[0].descriptor_manager.get(1)
                assert isinstance(stream1, ObjectWriteStream), "fd 1 of the first process should be a write stream"
                assert stream1.object.handle.startswith(
                    "intermediate_out_"
                ), "fd 1 of the first process should be an intermediate_out stream"

                stream2 = task.processes[1].descriptor_manager.get(0)
                print(stream2)
                assert isinstance(stream2, ObjectReadStream), "fd 0 of the second process should be a read stream"
                assert stream2.object.handle.startswith(
                    "intermediate_out_"
                ), "fd 0 of the second process should be an intermediate_out stream"
                assert (
                    stream1.object.handle == stream2.object.handle
                ), "fd 1 of the first process should be the same as fd 0 of the second process"
            if task.name.startswith("Custom grade result for "):
                assert isinstance(task, ScriptTask), "Custom task should be a script task"
                num_custom_scripts += 1
                assert len(task.input_registers) == 1, "Custom task should have one input register"
                assert len(task.output_registers) == 1, "Custom task should have one output register"
                assert len(task.objects) == 2, "Custom task should have two objects"
                assert task.objects[0].handle.startswith(
                    "intermediate_out_"
                ), "Custom task should have an intermediate_out object"
                assert task.objects[1].handle.startswith("user_out_"), "Custom task should have a user_out object"

        assert num_custom == 3, "Should have 3 custom execution tasks"
        assert num_custom_scripts == 3, "Should have 3 custom script tasks"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_user_out_workflow(get_package):
    for type in _get_run_types():
        print(f"From {type}")
        package_info: PackageInfo = get_package()
        package: Sinolpack = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        test = package.tests[0]

        op = package.get_user_out_operation(program, test)
        workflows = [wf for wf in op.get_workflow()]
        assert len(workflows) == 1
        workflow = workflows[0]

        assert len(workflow.observable_objects) == 1, "Should have just user out object"
        assert workflow.observable_objects[0].handle.startswith("user_out_"), "User out object should be user_out_"

        num_compiles = 0
        num_runs = 0
        for task in workflow.tasks:
            if task.name == f"Compile {program.path} using g++-12.2":
                assert len(task.processes) == 1, "Compile task should have one process"
                assert task.processes[0].image == "compiler:g++-12.2", "Compile task should use g++-12.2 image"
                num_compiles += 1
            elif task.name.startswith("Run solution for test"):
                num_runs += 1
                assert len(task.processes) == 1, "Run task should have one process"
                proc = task.processes[0]
                stdin_fd = proc.descriptor_manager.get(0)
                assert isinstance(stdin_fd, ObjectReadStream), "Run task should have stdin stream"
                stdout_fd = proc.descriptor_manager.get(1)
                assert isinstance(stdout_fd, ObjectWriteStream), "Run task should have stdout stream"
                assert stdout_fd.object.handle.startswith("user_out"), "Run task should have user_out stream"

        assert num_compiles == 1, "Should have one compile task"
        assert num_runs == 1, "Should have one run task"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["simple"], indirect=True)
def test_test_run_workflow(get_package):
    for type in _get_run_types():
        print(f"From {type}")
        package_info: PackageInfo = get_package()
        package: Sinolpack = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        test = package.tests[0].in_file

        op = package.get_test_run_operation(program, test)
        workflows = [wf for wf in op.get_workflow()]
        assert len(workflows) == 1
        workflow = workflows[0]

        assert len(workflow.observable_objects) == 1, "Should have just user out object"
        out_obj = workflow.observable_objects[0]
        assert out_obj.handle == f"test_run_{program.filename}", "User out object should be user_out_<filename>"

        assert len(workflow.tasks) == 2, "Should have two tasks"
        assert workflow.tasks[0].name == f"Compile {program.path} using g++-12.2", "First task should be compile"
        assert workflow.tasks[1].name == f"Run solution for test", "Second task should be run"
        exec_task = workflow.tasks[1]
        assert isinstance(exec_task, ExecutionTask), "Second task should be an execution task"
        assert len(exec_task.processes) == 1, "Run task should have one process"
        proc = exec_task.processes[0]
        stdin_fd = proc.descriptor_manager.get(0)
        assert isinstance(stdin_fd, ObjectReadStream), "Run task should have stdin stream"
        assert stdin_fd.object.handle == test.path, "Run task should have stdin stream"
        stdout_fd = proc.descriptor_manager.get(1)
        assert isinstance(stdout_fd, ObjectWriteStream), "Run task should have stdout stream"
        assert stdout_fd.object.handle == out_obj.handle, "Run task should have stdout stream"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["extra_files"], indirect=True)
def test_extra_files(get_package):
    for type in _get_run_types():
        print(f"From {type}")
        for i in range(2):
            package_info: PackageInfo = get_package()
            # On the second pass, change some config values to strings
            if i == 1:
                config = yaml.safe_load(open(os.path.join(package_info.path, "config.yml")).read())
                config["extra_compilation_args"]["cpp"] = "extlib.h"
                open(os.path.join(package_info.path, "config.yml"), "w").write(yaml.dump(config))

            package: Sinolpack = _get_package(package_info, type)
            common_checks(package_info, package)

            program = package.main_model_solution

            op = package.get_run_operation(program)
            workflows = [wf for wf in op.get_workflow()]
            assert len(workflows) == 1
            workflow = workflows[0]

            print(workflow.external_objects)
            assert len(workflow.external_objects) == 5
            extlib_h = None
            extlib_py = None
            for obj in workflow.external_objects:
                if obj.handle.endswith("extlib.h"):
                    extlib_h = obj
                elif obj.handle.endswith("extlib.py"):
                    extlib_py = obj
            assert extlib_h is not None, "Should have extlib.h as external object"
            assert extlib_py is not None, "Should have extlib.py as external object"

            for task in workflow.tasks:
                if isinstance(task, ExecutionTask):
                    if task.name == f"Compile {program.path} using g++-12.2":
                        assert task.filesystem_manager.len() == 2
                        ext_fs = task.filesystem_manager.get_by_id(1)
                        assert isinstance(ext_fs, ObjectFilesystem), "Should have object filesystem with external file"
                        assert ext_fs.object.handle == extlib_h.handle, "Should have extlib.h as external file"

                        assert task.mountnamespace_manager.len() == 1, "Should have one mount namespace"
                        assert (
                            len(task.mountnamespace_manager.get_by_id(0).mountpoints) == 2
                        ), "Should have two mount points"

                        proc = task.processes[0]
                        assert "extlib.h" in proc.arguments, "Should have extlib.h in arguments"
                    elif task.name.startswith("Run solution for test"):
                        assert task.filesystem_manager.len() == 2
                        ext_fs = task.filesystem_manager.get_by_id(1)
                        assert isinstance(ext_fs, ObjectFilesystem), "Should have object filesystem with external file"
                        assert ext_fs.object.handle == extlib_py.handle, "Should have extlib.py as external file"

                        assert task.mountnamespace_manager.len() == 1, "Should have one mount namespace"
                        assert (
                            len(task.mountnamespace_manager.get_by_id(0).mountpoints) == 2
                        ), "Should have two mount points"

            # Check that python compilation doesnt have extlib.h in compilation args.
            program = None
            print("Looking for extlib.py")
            for ms in package.model_solutions:
                print(f"Checking {ms}")
                if ms["file"].filename.endswith("ext.py"):
                    program = ms["file"]
                    break
            assert program is not None, "Should have ext.py as model solution"
            op = package.get_run_operation(program)
            workflows = [wf for wf in op.get_workflow()]
            assert len(workflows) == 1

            for task in workflows[0].tasks:
                if isinstance(task, ExecutionTask):
                    if task.name == f"Compile {program.path} using python":
                        assert task.filesystem_manager.len() == 2
                        ext_fs = task.filesystem_manager.get_by_id(1)
                        assert isinstance(ext_fs, ObjectFilesystem), "Should have object filesystem with external file"
                        assert ext_fs.object.handle == extlib_py.handle, "Should have extlib.py as external file"

                        assert task.mountnamespace_manager.len() == 1, "Should have one mount namespace"
                        assert (
                            len(task.mountnamespace_manager.get_by_id(0).mountpoints) == 2
                        ), "Should have two mount points"

                        proc = task.processes[0]
                        assert "extlib.h" not in proc.arguments, "Should not have extlib.h in arguments"


@pytest.mark.django_db
@pytest.mark.parametrize("get_package", ["extra_files"], indirect=True)
def test_extra_files_in_workflow(get_package):
    for type in _get_run_types():
        print(f"From {type}")

        package_info: PackageInfo = get_package()
        with open(os.path.join(package_info.path, "workflows.json"), "w") as f:
            f.write(
                json.dumps(
                    {
                        "grade_group": {
                            "name": "Grade group workflow",
                            "observable_objects": [],
                            "external_objects": ["<EXTRA_FILE:dir/some_file.txt>"],
                            "registers": 0,
                            "observable_registers": 0,
                            "tasks": [
                                {
                                    "name": "Custom grade group",
                                    "type": "script",
                                    "reactive": False,
                                    "input_registers": [],
                                    "output_registers": [],
                                    "objects": ["<EXTRA_FILE:dir/some_file.txt>"],
                                    "script": "",
                                }
                            ],
                        }
                    }
                )
            )

        package_info: PackageInfo = get_package()
        package: Sinolpack = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        op = package.get_run_operation(program)
        workflows = [wf for wf in op.get_workflow()]
        assert len(workflows) == 1
        workflow = workflows[0]

        found = False
        for task in workflow.tasks:
            if isinstance(task, ScriptTask) and task.name == "Custom grade group":
                found = True
                assert len(task.objects) == 1, "Should have one object"
                assert task.objects[0].handle.endswith("some_file.txt"), "Should have some_file.txt as object"
                assert "EXTRA_FILE" not in task.objects[0].handle, "Should not have EXTRA_FILE in handle"

        assert found, "Should have found the custom grade group workflow"

        found = False
        for obj in workflow.external_objects:
            if obj.handle.endswith("some_file.txt"):
                found = True
                assert "EXTRA_FILE" not in obj.handle, "Should not have EXTRA_FILE in handle"

        assert found, "The extra file should be an external object"

        # Now, test if workflow creation fails when the file is not in the package
        with open(os.path.join(package_info.path, "workflows.json"), "w") as f:
            f.write(
                json.dumps(
                    {
                        "grade_group": {
                            "name": "Grade group workflow",
                            "observable_objects": [],
                            "external_objects": ["<EXTRA_FILE:non_existent>"],
                            "registers": 0,
                            "observable_registers": 0,
                            "tasks": [
                                {
                                    "name": "Custom grade group",
                                    "type": "script",
                                    "reactive": False,
                                    "input_registers": [],
                                    "output_registers": [],
                                    "objects": ["<EXTRA_FILE:non_existent>"],
                                    "script": "",
                                }
                            ],
                        }
                    }
                )
            )

        package_info: PackageInfo = get_package()
        package: Sinolpack = _get_package(package_info, type)
        common_checks(package_info, package)

        program = package.main_model_solution
        op = package.get_run_operation(program)
        with pytest.raises(WorkflowCreationError):
            _ = [wf for wf in op.get_workflow()]
