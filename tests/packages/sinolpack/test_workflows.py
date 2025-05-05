import os

import pytest

import sio3pack
from sio3pack import LocalFile
from sio3pack.packages.package.configuration import SIO3PackConfig
from sio3pack.workflow import ExecutionTask, ScriptTask
from sio3pack.workflow.execution import ObjectReadStream, ObjectWriteStream
from tests.packages.sinolpack.utils import common_checks
from tests.fixtures import PackageInfo, get_package


@pytest.mark.parametrize("get_package", ["simple", "inwer"], indirect=True)
def test_unpack_workflows(get_package):
    package_info: PackageInfo = get_package()
    package = sio3pack.from_file(package_info.path, SIO3PackConfig.detect())
    common_checks(package_info, package)

    op = package.get_unpack_operation()
    assert op is not None
    workflows = []
    for wf in op.get_workflow():
        print(wf.name)
        workflows.append(wf)

    if package_info.task_id == "abc":
        # We expect 2 workflows: compile checker and outgen
        assert len(workflows) == 2
        assert workflows[0].name == "Compile checker"
        assert workflows[1].name == "Outgen tests"
    elif package_info.task_id == "wer":
        # We expect 3 workflows: compile checker, outgen and inwer
        assert len(workflows) == 3
        assert workflows[0].name == "Compile checker"
        assert workflows[1].name == "Outgen tests"
        assert workflows[2].name == "Inwer"


@pytest.mark.parametrize("get_package", ["run"], indirect=True)
def test_run_workflow(get_package):
    package_info: PackageInfo = get_package()
    package = sio3pack.from_file(package_info.path, SIO3PackConfig.detect())
    common_checks(package_info, package)

    program = LocalFile(os.path.join(package.rootdir, "prog", "run.cpp"))
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
                assert task.filesystem_manager.len() == 4, "Checker task should have 4 filesystems: checker, in, out and user_out"
                proc = task.processes[0]
                assert proc.descriptor_manager.size() == 1, "Checker task should have one descriptor"
                stdout_fd = proc.descriptor_manager.get(1)
                assert isinstance(stdout_fd, ObjectWriteStream), "Checker task should have stdout stream"
            else:
                raise ValueError(f"Unknown task name: {task.name}")
        elif isinstance(task, ScriptTask):
            print(task.name)
            if task.name.startswith("Grade test"):
                num_grade_tests += 1
                print(task.to_json())
                assert len(task.input_registers) == 2, "Grade test task should have 2 input registers: checker result and user result"
                assert len(task.objects) == 1, "Grade test task should have one object: user_out"
                assert len(task.output_registers) == 1, "Grade test task should have one output register: grading result"
            elif task.name.startswith("Grade group"):
                num_grade_group += 1
                # In this task, there is only one test in each group
                assert len(task.input_registers) == 1, "Grade group task should have one input register: grading result of the test"
                assert len(task.output_registers) == 1, "Grade group task should have one output register: grading result"
            elif task.name == "Grade run":
                num_grade_all += 1
                assert len(task.input_registers) == 3, "Grade run task should have three input registers: grading result of the groups"
                assert len(task.output_registers) == 1, "Grade run task should have one output register: grading result"
            else:
                raise ValueError(f"Unknown task name: {task.name}")
        else:
            raise ValueError(f"Unknown task type: {type(task)}")

    assert compile_ok, "Compile task should be ok"
    assert num_runs == num_runs_checker == num_grade_tests == 3, "Should have 3 runs"
    assert num_grade_group == 3, "Should have 3 groups"
    assert num_grade_all == 1, "Should have one grade run"
