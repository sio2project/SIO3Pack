Usage guide
===========

This library allows to interact with packages supported by SIO2 system. It's used in two important components of SIO2:

- `OIOIOI <https://github.com/sio2project/oioioi>`_, which is the web interface for SIO2 system,
- `sinol-make <https://github.com/sio2project/sinol-make>`_, which is the local tool for testing packages.

The purpose of this library is to keep the code for package management in one place, so that it can be reused in both components.
This will also allow developers to write their own tools that can interact with SIO2 packages.

Supported package types
-----------------------

Currently, this library supports the following package types:

- `sinolpack` -- a package format originally used by SIO2 system, which is a simple archive format with metadata,
  and is used for most packages in SIO2 system.

Next planned package types to be supported are:

- `sinol3pack` -- a new package format that is being developed for SIO2/SIO3 system, which will be a more advanced format
  with better support for metadata and dependencies,
- Codeforces packages -- a package format used by `Codeforces system <https://codeforces.com/>`_, which is a popular
  competitive programming platform.

Installation
------------

To install the library, you can use `pip`. There are two ways to install it, depending on the way you want to use it:

- if you want to use the library locally, without the need for Django, you can install it with the following command:

  .. code-block:: shell

    pip install sio3pack

- if you want to use the library with Django support, for example when developing OIOIOI, you can install it with the following command:

  .. code-block:: shell

    pip install sio3pack[django]

Initializing without Django support
-----------------------------------
When using SIO3Pack without Django support, there is only one way to initialize a package, which is by using the
:py:func:`sio3pack.from_file` function. This function takes a file path to a directory with the package or a archived
package file, and returns an instance of :py:class:`sio3pack.packages.package.Package` class, which can be used to
interact with the package.

This class is an abstract base class, so for different package types, you will receive different subclasses of this class.
For example for `sinolpack` packages, you will get an instance of :py:class:`sio3pack.packages.sinolpack.Sinolpack` class.

Example when importing a `sinolpack` package:

.. code-block:: python

  import sio3pack
  from sio3pack.packages.sinolpack import Sinolpack


  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")

  print(package.full_name)  # Prints the full title of the package

The :py:func:`sio3pack.from_file` function can also take an optional argument `configuration`, which is an instance
of :py:class:`sio3pack.packages.package.SIO3PackConfig` class. For local usage, this class mainly provides available
compilers. It is possible to automatically detect the configuration by using the :py:meth:`sio3pack.packages.package.SIO3PackConfig.detect`
method, which will try to detect the configuration based on the current environment. Example usage:

.. code-block:: python

  import sio3pack
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.packages.package import SIO3PackConfig

  configuration = SIO3PackConfig.detect()
  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package", configuration=configuration)

  print(package.full_name)  # Prints the full title of the package

Initializing with Django support
--------------------------------

When using SIO3Pack with Django support, you can initialize a package using the same :py:func:`sio3pack.from_file` function,
but you can also use the :py:func:`sio3pack.from_db` function, which allows you to initialize a package from the database.

After initializing the package from file, you can use the :py:meth:`sio3pack.packages.package.Package.save_to_db` method
to save the package to the database. This method will create a new package in the database, or update an existing one if
it already exists.

The :py:class:`sio3pack.packages.package.SIO3PackConfig` class can also take the Django settings, which is useful when you want to
use the library with Django support.

The important distinction between a package from file and a package from the database is that the package from database
is lazy-loaded, meaning that the metadata and files are not loaded until they are accessed. This is useful for
saving memory and improving performance, especially for OIOIOI.

Example usage:

.. code-block:: python

  import sio3pack
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.packages.package import SIO3PackConfig

  from django.conf import settings


  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  problem_id = 1  # The `save_to_db` functions requires a problem ID to save the package to the database
  package.save_to_db(problem_id)


  configuration = SIO3PackConfig.detect()
  configuration.django_settings = settings  # Set the Django settings for the configuration
  from_db: Sinolpack = sio3pack.from_db(problem_id, configuration=configuration)
  print(from_db.full_name)  # Prints the full title of the package from the database

Interacting with workflows
--------------------------

The most important part of the new packages specification are the workflows, which are a set of steps that can be
executed by the sio3workers. There are default workflows for all types of packages, but you can also create your own
workflows by creating a `workflows.json` file in the package directory. For more information, read the
:doc:`workflows section <workflows>` of the documentation.

There are a couple of important workflows that can be used:

- unpack workflow -- for the first time unpacking the package, which will generate tests and verify them
- run workflow -- for running a program on the tests from the package
- generate user out workflow -- for generating an output of user's program on a test from the package
- test run workflow -- for generating an output for user's program on a user-provided test

Each method for generating workflows returns an instance of :py:class:`sio3pack.workflow.WorkflowOperation` class,
which can be used to get the workflows. This class has a method :py:meth:`sio3pack.workflow.WorkflowOperation.get_workflow`,
which yields instances of :py:class:`sio3pack.workflow.Workflow` class until there are workflows to be run.
The :py:class:`sio3pack.workflow.Workflow` class can be passed to a sio3worker executor, which will then run the workflow
and return the results. After each workflow run, the results should be passed to :py:meth:`sio3pack.workflow.WorkflowOperation.return_results`
method. Example usage of a workflow operation:

.. code-block:: python

  import sio3pack, sio3worker
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.workflow import WorkflowOperation

  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  wf_op: WorkflowOperation = package.get_some_workflow_operation()

  for workflow in wf_op.get_workflow():
    results = sio3worker.run_workflow(workflow)  # This will run the workflow using the sio3worker executor
    wf_op.return_results(results)  # This will return the results of the workflow to the operation


Unpack workflow
~~~~~~~~~~~~~~~

This workflow should be used after initializing a package from file. It will generate tests, verify them and save the
information about the tests on the package. This workflow uses these sub-workflows:

- `ingen` -- for generating input tests
- `outgen` -- for generating output tests
- `inwer` -- for verifying the input tests

These workflows can be created by calling the :py:meth:`sio3pack.packages.package.Package.get_unpack_operation` method on
the package instance. This method will return the workflow operation. Example usage:

.. code-block:: python

  import sio3pack, sio3worker
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.workflow import WorkflowOperation

  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  unpack_op: WorkflowOperation = package.get_unpack_operation()

  for workflow in unpack_op.get_workflow():
    results = sio3worker.run_workflow(workflow)  # This will run the workflow using the sio3worker executor
    unpack_op.return_results(results)  # This will return the results of the workflow to the operation

  # After unpacking, you can save the package to the database
  package.save_to_db(problem_id)

Run workflow
~~~~~~~~~~~~

This workflow is used for running a program on the tests from the package. It can be created by calling the
:py:meth:`sio3pack.packages.package.Package.get_run_operation` method on the package instance. This method requires
a `program` argument, which is an instance of :py:class:`sio3pack.files.File` class, which represents the program to be run.
It also has an optional argument `tests`, which allows to specify a list of tests to be run. If not specified,
all tests from the package will be used. Example usage:

.. code-block:: python

  import sio3pack, sio3worker
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.files import File
  from sio3pack.workflow import WorkflowOperation

  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  program: File = package.get_program("main")  # Get the main program file from the package
  run_op: WorkflowOperation = package.get_run_operation(program)

  for workflow in run_op.get_workflow():
    results = sio3worker.run_workflow(workflow)  # This will run the workflow using the sio3worker executor
    run_op.return_results(results)  # This will return the results of the workflow to the operation

User out workflow
~~~~~~~~~~~~~~~~~

This workflow is used for generating an output of user's program on a test from the package. It can be created by
calling the :py:meth:`sio3pack.packages.package.Package.get_user_out_operation` method on the package instance.
This method requires two arguments: `program` and `test`. The `program` argument is an instance of
:py:class:`sio3pack.files.File` class, which represents the user's program to be run, and the `test` argument is
an instance of :py:class:`sio3pack.test.Test` class, which represents the test to be run. Example usage:

.. code-block:: python

  import sio3pack, sio3worker
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.files import File
  from sio3pack.test import Test
  from sio3pack.workflow import WorkflowOperation

  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  program: File = package.get_program("main")  # Get the main program file from the package
  test: Test = package.tests[0]  # Get the first test from the package
  user_out_op: WorkflowOperation = package.get_user_out_operation(program, test)

  for workflow in user_out_op.get_workflow():
    results = sio3worker.run_workflow(workflow)  # This will run the workflow using the sio3worker executor
    user_out_op.return_results(results)  # This will return the results of the workflow to the operation

Test run workflow
~~~~~~~~~~~~~~~~~

This workflow is used for generating an output for user's program on a user-provided test. It can be created by
calling the :py:meth:`sio3pack.packages.package.Package.get_test_run_operation` method on the package instance.
This method requires two arguments: `program` and `test`. Both arguments are instances of
:py:class:`sio3pack.files.File` class, where `program` represents the user's program to be run, and `test`
represents the user-provided test to be run. Example usage:

.. code-block:: python

  import sio3pack, sio3worker
  from sio3pack.packages.sinolpack import Sinolpack
  from sio3pack.files import LocalFile
  from sio3pack.workflow import WorkflowOperation

  package: Sinolpack = sio3pack.from_file("path/to/sinolpack/package")
  program: File = package.get_program("main")  # Get the main program file from the package
  user_test: LocalFile = LocalFile("path/to/user/test")  # User-provided test file
  test_run_op: WorkflowOperation = package.get_test_run_operation(program, user_test)

  for workflow in test_run_op.get_workflow():
    results = sio3worker.run_workflow(workflow)  # This will run the workflow using the sio3worker executor
    test_run_op.return_results(results)  # This will return the results of the workflow to the operation

More information
----------------

For more information on how to use the library, you can check the documentation for the specific package types, such as
:py:class:`sio3pack.packages.sinolpack.Sinolpack`. You can also check the :doc:`workflows section <workflows>` for examples
of how to implement your own workflows using the library.
