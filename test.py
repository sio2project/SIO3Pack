import json

from deepdiff import DeepDiff

from sio3pack.workflow import Workflow, ExecutionTask

with open("example_workflows/simple_run.json", "r") as f:
    data = json.load(f)

workflow = Workflow.from_json(data)
print(workflow)

print(DeepDiff(data, workflow.to_json()))
