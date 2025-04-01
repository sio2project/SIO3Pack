Sinolpack documentation
=======================

Sinolpack is a package standard currently used in SIO2.

Package structure
-----------------

For a package to be considered a Sinolpack, it must
have at least the following structure:

.. code-block:: none

  abc.tar.gz
  └── abc/
      ├── in/
      └── out/

The package must have a top-level directory, which is the
short name (task id) of the package. This directory must
contain two subdirectories: `in` and `out`.

The package can be compressed in these formats: `tar.gz`,
`tgz` or `zip`.

Below are the descriptions of all possible files and
directories in a Sinolpack.

`in` directory
~~~~~~~~~~~~~~

The `in` directory contains all input tests for the package.
Each test has to have a unique name: `<short_name><test id>.in`.
Test id is a group number and an optional string of letters.
Group number 0 is considered the example group -- points are
not awarded for these tests and results are usually shown
to the user.

For example, the following files are valid input tests for a
package with short name `abc`:

- `abc0.in` -- example test
- `abc0a.in` -- also an example test
- `abc1ab.in` -- test from group 1

`out` directory
~~~~~~~~~~~~~~~

The `out` directory contains all output tests for the package.
Their names are the same as the input tests, but with the
extension `.out`.

`config.yml` file
~~~~~~~~~~~~~~~~~

The `config.yml` file contains the configuration of the package.
It is located in the root of the package:

.. code-block:: none

  abc.tar.gz
  └── abc/
      ├── config.yml
      ├── in/
      └── out/

The configuration file is a YAML file with the following possible
fields:

- `title` -- the title of the package
- `title_<lang>` -- the title of the package in a specific language
- `scores` -- specifies the number of points for each test group.
  The key is the group number and the value is the number of points.
  By default, points are distributed evenly among the groups (if
  number of groups doesn't divide 100, then the last groups will
  have the remaining points). Group 0 always has zero points.
  Example:

  .. code-block:: yaml

    scores:
      1: 20
      2: 30
      3: 100

  In this example, group 1 has 20 points, group 2 has 30 points and
  group 3 has 100 points. As shown, the points don't have to sum up
  to 100.
- `time_limit` -- the time limit for all tests in milliseconds
- `time_limits` -- allows specifying time limits per group or
  per test. The key is the group number or the test id and the
  value is the time limit in milliseconds. The most specific
  time limit is used. Example:

  .. code-block:: yaml

    time_limit: 500
    time_limits:
      1: 1000
      2: 2000
      2b: 3000

  In this example, group 1 has a time limit of 1000 ms, group 2
  has a time limit of 2000 ms, except for test 2b which has a
  time limit of 3000 ms. All other tests have a time limit of 500 ms.

- `memory_limit` -- the memory limit for all tests in kB.
- `memory_limits` -- same as `time_limits`, but for memory limits.
  Specified in kB.
- `override_limits` -- allows overriding time or memory limits per
  programming language. The key is the language and the value is
  a dictionary with `time_limit`, `time_limits`, `memory_limit` and
  `memory_limits` fields. Not all fields have to be specified. Example:

  .. code-block:: yaml

    override_limits:
      py:
        time_limit: 1000
        memory_limit: 256000
      cpp:
        time_limits:
          1: 2000
          2: 3000
        memory_limit: 512000

  In this example, Python programs have a time limit of 1000 ms and
  a memory limit of 256 MB. C++ programs have a time limit of 2000 ms
  for group 1 and 3000 ms for group 2, and a memory limit of 512 MB.
- `extra_compilation_args` -- allows specifying extra compilation
  arguments per programming language. The key is the language and
  the value is a list of arguments or a single value. Example:

  .. code-block:: yaml

    extra_compilation_args:
      cpp:
        - -std=c++11
        - -O2
      py: single_value

  In this example, C++ programs are compiled with the `-std=c++11`
  and `-O2` arguments. Python programs are compiled with a single
  value argument.

- `extra_compilation_files` -- an array of files that should be
  included in the compilation process. The files are relative to
  the `prog/` directory. Example:

  .. code-block:: yaml

    extra_compilation_files:
      - prog/abclib.cpp
      - prog/abclib.py

- `extra_execution_files` -- an array of files that should be
  present when the program is executed. The files are relative
  to the `prog/` directory.

The `config.yml` can also contain other fields used by various
tools, like `sinol-make` which uses fields starting with
`sinol_`. These fields are ignored by SIO2 and are described
`here <https://github.com/sio2project/sinol-make/blob/main/example_package/config.yml>`_.

`prog` directory
~~~~~~~~~~~~~~~~

The `prog` directory contains all source files for the package.
The source files can be in any language. Here is a list of
common files in the `prog` directory:

- model solutions -- optional files that are used to see
  if grading is correct. The regex expression for them
  is `<short name>[bs]?[0-9]*(_.*)?\.(<languages>)`,
  where languages is a string of language extensions
  seperated by `|`. If the file contains a `b` in the
  first group, it is considered a bad solution and
  if it contains `s`, it's a slow solution. This
  information is only used to sort the model solutions
  in the results.

  A model solution named `<short name>.<language>` is
  used for generating output tests, so it should be
  a correct solution.

- `<short name>ingen.<language>` -- optional file that
  is used to generate input tests. It is run in the
  `in` directory and should generate input tests in
  the format described above.

- `<short name>inwer.<language>` -- optional file that
  is used to verify the correctness of the input tests.
  It is run for all input tests with it's first argument
  being the filename of the input test and on it's standard
  input the input test. If the test is correct, it should
  exit with code 0, otherwise with a non-zero code.

`doc` directory
~~~~~~~~~~~~~~~

The `doc` directory contains all documents for the package.
SIO2 uses the `<short name>zad.pdf` file as the task
description. The files `<short name>zad<language>.pdf` are
used as task descriptions in specific languages.

Some SIO2 instances allow compiling the task description
from a LaTeX file. In that case, the LaTeX file should be
named `<short name>zad.tex`. The LaTeX file can also be
in a specific language, in which case it should be named
`<short name>zad<language>.tex`.

The task description can also be in HTML format. In that
case, the files are in an archive `<short name>zad.html.zip`.
The HTML archive can also be for a specific language,
in which case it should be named `<short name>zad<language>.html.zip`.

`attachments` directory
~~~~~~~~~~~~~~~~~~~~~~~

Files from the `attachments` directory are shown in the
`Files` section on SIO2.


Task types
----------

Sinolpack isn't very flexible, but supports various task
types: normal, interactive (via library or IO) and
output-only. The task type is determined by the presence
of specific files in the package.

Normal task type
~~~~~~~~~~~~~~~~

Normal tasks are the most common type of tasks. They have
model solutions, input and output tests and can have a
checker for grading submissions.

This task type is used when no other task type is detected.

Custom files:

- `prog/<short name>chk.<language>` -- output checker for
  the task. It is run with the first path to the input
  file, the second path to the user out file and the third
  path to the correct out file. If the checker exits with
  code greater than 2, the submission gets a System Error.
  The output of the checker must have at least one file,
  which is the result of the grading. If it's `OK`, the
  submission is correct, otherwise it's incorrect. In the
  second line of the output, the checker can print an optional
  comment that will be shown to the user. In the third line,
  the checker can print the number of points the submission
  got. The third line is passed to Python's
  `fractions.Fraction <https://docs.python.org/3/library/fractions.html>`_
  constructor, so it can be a fraction.

Interactive (via library) task type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This task type is actually handled as a normal task type,
but it uses `extra_compilation_args` and `extra_compilation_files`
to specify the library that should be linked with the program.
The library reads from the standard input and writes the results
to the standard output.

Interactive (via IO) task type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This task type is used when the package contains the
`prog/<short name>soc.<language>` file. This file is
used to communicate with the user's program and grade
it.

This task type can have a field `num_processes` in the
`config.yml` file. This field specifies the number of
processes that will be run in parallel. The default
value is 1.

The `soc` program will be run with the following arguments:

- number of the processes
- pairs of numbers of file descriptors for writing and reading
  to the user's program

The `soc` program on the standard input will receive the
input test and on the standard output should write the
grading result. The output is the same as for the normal
task type's checker.

Output-only task type
~~~~~~~~~~~~~~~~~~~~~

I don't remember:(


How the package is processed
----------------------------

When a package is uploaded to SIO2, it is processed in the
following way:

1. The package is extracted to a temporary directory.
2. The `config.yml` file is read and the configuration is
   stored in the database.
3. Title and translated titles are stored in the database.
   If the title is not specified in `config.yml`, the title
   is taken from the LaTeX task description (if present) from
   the `\title` command. Only main title is taken from LaTeX,
   translated titles can only be specified in `config.yml`.
4. Extra compilation and execution files are saved in the
   file storage. If any of the files are missing, the package
   is considered invalid.
5. All files from `prog/` are saved as an archive in the
   file storage.
6. Statements are processed and saved. If LaTeX files are
   present and the SIO2 instance allows compiling LaTeX,
   the compiled PDF is saved in the file storage.
7. Tests are generated, limits are saved and scores for
   groups are assigned. There is one legacy method for
   setting memory limits, which is to specify the limit
   in LaTeX in the `\RAM` command. The actual memory
   limit is then calculate as such:
   `(value + (value + 31) // 32) * 1000`. This method is
   deprecated and should not be used.
8. Checker program is saved in the file storage (if present).
9. If the task type is interactive via IO, the `soc` program
   is saved in the file storage.
10. Model solutions are created and saved in the database.
11. Attachments are saved in the file storage.
12. The package is marked as processed.
