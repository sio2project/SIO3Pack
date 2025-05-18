import json
import os

import pytest
from deepdiff import DeepDiff

from sio3pack.workflow import Workflow


def test_workflow_parsing():
    workflows_dir = os.path.join(os.path.dirname(__file__), "..", "..", "example_workflows")
    for file in os.listdir(workflows_dir):
        if not os.path.splitext(file)[1] == ".json":
            continue

        # This is an example configuration file, not a workflow file
        if file.endswith("workflows.json"):
            continue

        print(f"Parsing {file}")
        data = json.load(open(os.path.join(workflows_dir, file)))
        workflow = Workflow.from_json(data)
        assert workflow.to_json() == data, f"Failed for {file}. Diff: {DeepDiff(data, workflow.to_json())}"


def test_workflow_to_int_regs():
    workrflow = os.path.join(os.path.dirname(__file__), "..", "..", "example_workflows", "run.json")
    data = json.load(open(workrflow))
    workflow = Workflow.from_json(data)
    with pytest.raises(TypeError):
        workflow.to_json(to_int_regs=True)

    string_regs = os.path.join(os.path.dirname(__file__), "..", "..", "example_workflows", "string_regs.json")
    data = json.load(open(string_regs))
    workflow = Workflow.from_json(data)
    # Should not raise an error
    workflow.to_json(to_int_regs=True)
