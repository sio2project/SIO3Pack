SIO3Worker workflows documentation
==================================

This document provides an overview of the workflow's specification
and how to use it effectively.


Workflow Specification
----------------------

A workflow is a collection of tasks that can run programs, execute Lua scripts, write objects,
read and write from registers, and perform various other operations. Workflows are defined by a
JSON file that describes the tasks, their dependencies, and the data they use.

Objects
~~~~~~~

Objects are files that can be provided from file storage, can be read of written by workflows and
can be saved to file storage. An object can be a compiled executable, source code or a test.
Objects are identified by their handle and can be referenced in the workflow.

There are three types of objects:

- **external object** -- an object that is provided from file storage, such as a compiled executable or source code.
  These objects can be used by workflows. These objects have to be specified in the `external_objects` key in
  the workflow JSON file. This is an array of handles of external objects that can be used by the workflow.
- **observable object** -- an object that is created by the workflow and saved to the file storage.
  This type of object is for example a compiled executable or generated tests. These objects have to be
  specified in the `observable_objects` key in the workflow JSON file. This is an array of handles of observable
  objects that can be used by the workflow.
- **normal object** -- any other object. This type of object can be created by workflow and after finishing
  they are deleted. An example of this object is a user's generated output which is only used by a checker.
  These objects aren't specified in the workflow definition. They can be specified in tasks.

Registers
~~~~~~~~~

Registers are used to store any data that can be used by workflow. Only one task can write to a register, but
multiple tasks can read from it. Registers are identified by their number, starting from 0.

There are two types of registers:

- **observable register** -- after the workflow finishes, the value of this register is returned to the user.
  This type of register is used to store the final result of the workflow, such as the output of a program or
  the result of a test. These registers have numbers starting from 0. The number of observable registers has
  to be specified in the `observable_registers` key in the workflow definition.
- **normal register** -- this type of register is used to store intermediate results of the workflow. These registers
  can be used by any task in the workflow, but their values are not returned to the user. These registers have
  numbers starting from the number of observable registers. The total number of registers (including observable) has
  to be specified in the `registers` key in the workflow definition.

Tasks
~~~~~

Tasks are the building blocks of a workflow. Each task can perform a specific operation, such as running a program
or executing a Lua script. Tasks can depend on other tasks by using registers or objects. Tasks are defined in the
`tasks` key in the workflow definition, as an array of task definitions.

There are two types of tasks: script tasks and execution tasks. The type of task is specified by the `type` key in the
task definition (either `script` or `execution`).

Script Tasks
~~~~~~~~~~~~

Script tasks are tasks that execute Lua scripts. They can read and write to registers and read objects.

These keys are used to define script tasks:

- `type` -- the type of the task, which is `script` for script tasks.
- `name` -- the name of the task, used for debugging and logging.
- `input_registers` -- an array of register numbers that the task reads from.
- `output_registers` -- an array of register numbers that the task writes to.
- `objects` -- an array of object handles that the task reads from.
- `reactive` -- a boolean value that indicates whether the task is reactive. If true, the task will be executed
  whenever any of its input registers or objects change.
- `script` -- the Lua script to be executed by the task.

Execution Tasks
~~~~~~~~~~~~~~~

Execution tasks are tasks that can run processes, such as compiled executables or scripts. They can mount objects
inside filesystems, limit resources, mount in specific images, attach specific files to file descriptors, and more.
Security is mostly ensured by Linux namespaces, which isolate and limit the execution environment of the task.

These keys are used to define execution tasks:

- `type` -- the type of the task, which is `execution` for execution tasks.
- `name` -- the name of the task, used for debugging and logging.
- `channels` -- an array of configurations for pipes that the task uses. Each configuration is an object with the following keys:

  - `buffer_size` -- The maximum amount of data stored in the channel that has been written by
    the writer, but not yet read by the reader. This value must be positive.
  - `source_pipe` -- The pipe this channel will be reading from.
  - `target_pipe` -- The pipe this channel will be writing to.
  - `file_buffer_size` (optional) -- Controls whether this channel is backed by a file on the disk.
    A larger buffer may then be allocated on the disk.
  - `limit` (optional) -- Limits the maximum amount of data sent through the channel.
- `exclusive` -- a boolean value that indicates whether the task is exclusive. If true, the task will not run concurrently
  with other tasks.
- `hard_time_limit` -- the maximum amount of time the task can run, in seconds. If the task exceeds this limit, it will be terminated.
- `output_register` -- the register number that the execution results will be written to. This register will contain various
  information about the execution, such as the exit code, output, and error messages.
- `pid_namespaces` -- number of PID namespaces that the task will use. This is used to isolate the process tree of the task.
- `pipes` -- number of pipes that the task will use. Pipes are used for inter-process communication.
- `filesystems` -- an array of configuration for filesystems. Multiple filesystems can be mounted for a process.
  There are multiple types of filesystems:

  - Image filesystem -- a filesystem that is mounted from an image file. The configuration is an object with the following keys:

    - `type` -- the type of the filesystem, which is `image` for image filesystems.
    - `path` -- the path to the image file.
  - Empty filesystem -- a filesystem that is mounted as an empty directory. The configuration is an object with the following keys:

    - `type` -- the type of the filesystem, which is `empty` for empty filesystems.
  - Object filesystem -- a filesystem that is an object. The configuration is an object with the following keys:

    - `type` -- the type of the filesystem, which is `object` for object filesystems.
    - `object` -- the handle of the object that is used as a filesystem.
- `mount_namespaces` -- an array of mount namespace configurations. Each configuration is an object with the following keys:

  - `root` -- ?
  - `mountpoints` -- an array of mountpoint configurations. Each configuration can mount a filesystem at a given path,
    specyfing whether this file is writable. These keys are used to define mountpoints:

    - `source` -- index of the filesystem that is mounted at this mountpoint.
    - `target` -- the path where the filesystem is mounted.
    - `writable` -- a boolean value that indicates whether the mountpoint is writable.
- `resource_groups` -- an array of resource group configurations. Each configuration is an object with the following keys:

  - `cpu_usage_limit` -- the maximum percentage of CPU that the task can use. This value must be between 0 and 100 and is
    a floating point number.
  - `instruction_limit` -- the maximum number of cpu instructions that the task can execute. This value must be a positive integer.
  - `memory_limit` -- the maximum amount of memory that the task can use, in bytes. This value must be a positive integer.
  - `oom_terminate_all_tasks` -- a boolean value that indicates whether the task should terminate all tasks in the workflow
    if it runs out of memory. If true, all tasks will be terminated if the task runs out of memory.
  - `pid_limit` -- the maximum number of processes that the task can create. This value must be a positive integer.
  - `swap_limit` -- the maximum amount of swap memory that the task can use, in bytes. This value must be a non-negative integer.
  - `time_limit` -- the maximum amount of time the task can run, in microseconds. This value must be a positive integer.
- `processes` -- an array of process configurations. Each configuration is an object with the following keys:

  - `arguments` -- an array of strings that are passed as arguments to the process.
  - `environment` -- array of environment variables that are passed to the process. Each variable is a string in the format `KEY=VALUE`.
  - `image` -- the name of the image that is used to run the process.
  - `mount_namespace` -- the index of the mount namespace that the process will use.
  - `resource_group` -- the index of the resource group that the process will use.
  - `pid_namespace` -- the index of the PID namespace that the process will use.
  - `working_directorfy` -- the working directory of the process. This is the directory where the process will be executed.
  - `descriptors` -- a dictionary of file descriptors that are attached to the process. Each key is a file descriptor number
    (as a string) and each value is a stream. There are several types of streams (specified by `type` key):

    - file stream -- a stream which attaches a file to the file descriptor. It uses following keys:

      - `type` -- the type of the stream, which is `file` for file streams.
      - `filesystem` -- the index of the filesystem that contains the file.
      - `path` -- the path to the file in the filesystem.
      - `mode` -- the mode of the file, which can be `read`, `read_write`, `read_write_append`, `read_write_truncate`,
        `write`, `write_append`, or `write_truncate`.
    - null stream -- a stream that is a null device. It uses the following keys:

      - `type` -- the type of the stream, which is `null` for null streams.
    - object read stream -- a stream that allows reading from an object. It uses the following keys:

      - `type` -- the type of the stream, which is `object_read` for object read streams.
      - `handle` -- the handle of the object that is used as a stream.
    - object write stream -- a stream that allows writing to an object. It uses the following keys:

      - `type` -- the type of the stream, which is `object_write` for object write streams.
      - `handle` -- the handle of the object that is used as a stream.
    - pipe read stream -- a stream that allows reading from a pipe. It uses the following keys:

      - `type` -- the type of the stream, which is `pipe_read` for pipe read streams.
      - `pipe` -- the index of the pipe to read from.
    - pipe write stream -- a stream that allows writing to a pipe. It uses the following keys:

      - `type` -- the type of the stream, which is `pipe_write` for pipe write streams.
      - `pipe` -- the index of the pipe to write to.
  - `start_after` -- an array of process indices that this process will start after. This is used to define dependencies between processes.


Example workflows
------------------

Workflow examples can be found in the `example_workflows` directory in the SIO3Pack repository (`here <https://github.com/sio2project/SIO3Pack/tree/main/example_workflows>`_).
Every workflow in this directory was generated by SIO3Pack. Files ending with `_workflows.json` are examples of
user defined workflows, that can be used in packages. This is explained later in this document.

How workflow creation works in SIO3Pack
---------------------------------------

SIO3Pack allows a more object-oriented and user friendly way of creating workflows. It provides a set of classes that can
represent workflows, tasks, objects and all the other components of a workflow. These classes can be used to create workflows in a more intuitive way, without
having to write JSON files manually or worry about indexes or register numbers.

SIO3Pack allows joining multiple workflows together, allowing for writing small workflows that can be reused in larger workflows.
For example, a workflow for generating output tests is created by joining multiple workflows, which are responsible for
generating a single test. In SIO3Pack, registers can be named by strings, which makes it easier to understand the workflow
and allows joining workflows together without worrying about register numbers. All registers starting with `obsreg:`
are considered observable registers, and all other registers are considered normal registers. When a workflow is
converted to JSON, all registers are converted to numbers, and the observable registers are placed at the beginning of the register list.
SIO3Pack also has a simple templating system, for replacing strings in the workflow with values from the context.
Examples of such templates are `<TEST_ID>`, `<IN_TEST_PATH>` or special `<EXTRA_FILE:path>` and `<EXTRA_EXE:path>`,
which are replaced with the path to the extra file or executable in the workflow context.

Detailed documentation of SIO3Pack's workflow classes can be found in the :py:mod:`sio3pack.workflow` module documentation.
Below is a description on how to create own workflows for use in packages.

User Defined Workflows
----------------------

In a package, you can define your own workflows that will be used by SIO3Pack to generate workflows for the package.
These workflows are stored in `workflows.json` file in the package root directory. This files contains a dictionary
of workflows, where keys are names of workflows that you want to override and values are the workflow definitions.

Here are all currently used workflows and their descriptions:

- `compile_cpp` -- workflow for compiling C++ source code into an executable. It's used whenever a C++ file needs
  to be compiled into an executable. It uses the `g++` compiler and supports various options for compilation.
  It uses two templates: `<FILE>` for the path to the source file and `<OUT>` for the path to the output executable.
- `compile_python` -- workflow for compiling Python source code into an executable. It's used whenever a Python file needs
  to be compiled into an executable. It typically add she-bang to the file and makes it executable. Uses the same
  templates as `compile_cpp`.
- `compile_extra` -- a workflow that can be defined to compile any extra files. It is used during unpacking of package,
  before compiling any other common files, like checker. It doesn't have any extra templates.
- `ingen` -- workflow for generating input tests. It doesn't have any extra templates.
- `outgen_test` -- workflow for generating a single output test. This workflow is generated for each input test
  and then they are combined into a single workflow. Used templates:

  - `<IN_TEST_PATH>` -- the path to the input test file.
  - `<OUT_TEST_PATH>` -- the path to the output test file.
  - `<TEST_ID>` -- the ID of the test, which should be used to give unique names for registers.
  - `<COMPILED_OUTGEN_PATH>` -- the path to the compiled output generator executable.

  The execution output register should be named `r:ougen_res_<TEST_ID>`.
- `verify_outgen` -- a workflow which verifies if output generation was successful. Typically, this is a script
  task that checks if exit status of execution tasks are 0. It uses the following templates:

  - `<LUA_MAP_TEST_ID_REG>` -- a Lua template, which generates a map of test IDs to registers.
  - `<INPUT_REGS>` -- a template for use in `input_registers` key in script tasks. It is replaced with an array
    of registers which are output registers of output generation tasks (the `r:ougen_res_<TEST_ID>` registers).

  The output register of this workflow should be named `obsreg:result`, as it is a final task of outgen.

- `inwer` -- a workflow which runs inwer (input verification program) for one test. This workflow is generated
  for each input test and then they are combined into a single workflow. Used templates:

  - `<IN_TEST_PATH>` -- the path to the input test file.
  - `<TEST_ID>` --  the ID of the test, which should be used to give unique names for registers.
  - `<COMPILED_INWER_PATH>` -- path to the compiled inwer executable.

  The execution output register should be named `r:inwer_res_<TEST_ID>`.

- `verify_inwer` -- a workflow which verifies that input verification was successful. Typically, this is a script
  task that checks if exit status of execution tasks are 0. It uses the following templates:

  - `<LUA_MAP_TEST_ID_REG>` -- a Lua template, which generates a map of test IDs to registers.
  - `<INPUT_REGS>` -- a template for use in `input_registers` key in script tasks. It is replaced with an array
    of registers which are output registers of input verification tasks (the `r:inwer_res_<TEST_ID>` registers).

  The output register of this workflow should be named `obsreg:result`, as it is a final task of inwer.
- `run_test` -- a workflow which runs a program on a single test and grades the solution on this test. This workflow is
  generated for each input test, then they are grouped by test groups and finally results of workflows for grading groups
  are connected into grading the whole solution. Used templates:

  - `<TEST_ID>` -- the ID of the test, which should be used to give unique names for registers.
  - `<IN_TEST_PATH>` -- the path to the input test file.
  - `<OUT_TEST_PATH>` -- the path to the output test file.
  - `<SOL_PATH>` -- the path to the solution executable.

  The grading results for a test should be stored in `r:grade_res_<TEST_ID>` register.
- `grade_group` -- a workflow which grades a group of tests. Typically, this is a script task, which takes grading results
  as input and produces a grading for a given group. Used templates:

  - `<LUA_MAP_TEST_ID_REG>` -- a Lua template, which generates a map of test IDs to registers.
  - `<INPUT_REGS>` -- a template for use in `input_registers` key in script tasks. It is replaced with an array
    of registers which are output registers of grading tasks (the `r:grade_res_<TEST_ID>` registers).
  - `<GROUP_ID>` -- the ID of the group being graded, which should be used to give unique names for registers.

  The group grading results should be stored in `r:grup_grade_res_<GROUP_ID>` register.
- `grade_run` -- a workflow which grades the whole solution, based on grading results of groups. Typically, this is a
  script task that takes group grading results as input and produces a final grading for the solution. Used templates:

  - `<LUA_MAP_TEST_ID_REG>` -- a Lua template, which generates a map of group IDs to registers.
  - `<INPUT_REGS>` -- a template for use in `input_registers` key in script tasks. It is replaced with an array
    of registers which are output registers of group grading tasks (the `r:group_grade_res_<GROUP_ID>` registers).

  The final grading result should be stored in `obsreg:result` register, as it is a final task of grading the solution.
- `user_out` -- a workflow for generating program's output on a test. Used templates:

  - `<TEST_ID>` -- the ID of the test.
  - `<IN_TEST_PATH>` -- the path to the input test file.
  - `<SOL_PATH>` -- path to the program.

  This workflow should generate an observable object `user_out_<TEST_ID>`, as well as store execution results in
  `obsreg:result` register.
- `test_run` -- a workflow for generating program's output on a user-provided test. Used templates:

  - `<IN_TEST_PATH>` -- the path to the input file.
  - `<SOL_PATH>` -- path to the program.
  - `<USER_OUT_PATH>` -- a path to the user output file. This should be the final observable object.

  This workflow should generate an observable object `<USER_OUT_PATH>` as well as store execution results in
  `obsreg:result` register.
