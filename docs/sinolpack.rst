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
