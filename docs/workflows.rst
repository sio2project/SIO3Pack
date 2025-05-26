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
- `hard_time_limit` -- the maximum amount of time the task can run, in seconds. If the task exceeds this limit, it will be terminated.
- `mount_namespaces` -- an array of mount namespace configurations. Each configuration is an object with the following keys:
  - `root` -- ?
  - `mountpoints` -- an array of mountpoint configurations. Each configuration can mount a filesystem at a given path,
    specyfing whether this file is writable. These keys are used to define mountpoints:
