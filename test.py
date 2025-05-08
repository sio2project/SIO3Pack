# import json
#
# # from deepdiff import DeepDiff
#
# from sio3pack.workflow import Workflow, ExecutionTask
#
# with open("example_workflows/example.json", "r") as f:
#     data = json.load(f)
#
# workflow = Workflow.from_json(data)
# print(workflow)
#
# print(workflow.to_json(to_int_regs=True))
# # print(DeepDiff(data, workflow.to_json()))


import os, json, time

from sio3pack import LocalFile
from sio3pack.test import Test

# os.chdir(os.path.join(os.path.dirname(__file__), "tests", "test_packages", "abc"))
# os.chdir("/mnt/c/Users/maslo/oi/packages/lic")
os.chdir("/mnt/c/Users/maslo/oi/SIO3Pack/tests/test_packages/wfs")
import sio3pack
from sio3pack.packages.package.configuration import SIO3PackConfig, CompilerConfig

config = SIO3PackConfig(compilers_config={
    "cpp": CompilerConfig("cpp", "g++", "g++", ["-std=c++20", '-O3']),
}, extensions_config={
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hpp": "cpp",
})

start = time.time()
package = sio3pack.from_file(".", config)
end = time.time()
print("Time to load package:", end - start)


def ret_func(*args, **kwargs):
    print("ret_func", args, kwargs)


# wf_op = package.get_unpack_graph(ret_func)
# wf_op = package.get_run_graph(LocalFile("prog/lic.cpp"))
wf_op = package.get_run_operation(LocalFile("prog/wfs.cpp"))

# test = Test("1a", LocalFile("in/abc1a.in"), LocalFile("out/abc1a.out"), "1")
# wf_op = package.get_user_out_graph(LocalFile("prog/abc.cpp"), test, ret_func)
# wf_op = package.get_test_run_graph(LocalFile("prog/abc.cpp"), LocalFile("in/abc1a.in"), ret_func)

print(wf_op, type(wf_op))

if wf_op:
    start = time.time()
    for i, wf in enumerate(wf_op.get_workflow()):
        end = time.time()
        print(f"Time to load workflow {i}:", end - start)
        start = time.time()
        if i == 0:
            print(json.dumps(wf.to_json(to_int_regs=True)))
        # pass
        # print(json.dumps(wf.to_json(to_int_regs=True)))
