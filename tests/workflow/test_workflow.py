import os
import json
from deepdiff import DeepDiff

from sio3pack.workflow import Workflow


def test_workflow_parsing():
    workflows_dir = os.path.join(os.path.dirname(__file__), "..", "..", "example_workflows")
    for file in os.listdir(workflows_dir):
        if not os.path.splitext(file)[1] == ".json":
            continue
        print(f'Parsing {file}')
        data = json.load(open(os.path.join(workflows_dir, file)))
        workflow = Workflow.from_dict(data)
        assert workflow.to_dict() == data, f"Failed for {file}. Diff: {DeepDiff(data, workflow.to_dict())}"
