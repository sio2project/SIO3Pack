Development
===========

This section is intended for developers who want to contribute to the project or understand its inner workings.
It provides guidelines on how to set up the development environment, run tests, and contribute code.

Setting Up the Development Environment
--------------------------------------

If you want to develop or run tests without Django support, you can use the following command:

.. code-block:: bash

    pip install -e .[tests]
    pip uninstall django pytest-django

This will install the package in editable mode, without Django support. Uninstall Django and pytest-django to make sure
that the tests run without Django support.

If you want to run tests with Django support, you can use the following command:

.. code-block:: bash

    pip install -e .[django,tests,django_tests]

This will install the package in editable mode with Django support, along with the necessary testing dependencies.

Running Tests
-------------

To run the tests, you can use the following command:

.. code-block:: bash

    pytest -v

The tests can also be run in parallel using the `pytest-xdist` plugin. To do this, you can use the following command:

.. code-block:: bash

    pytest -v -n auto

You can also run coverage reports to see how much of the code is covered by tests. To do this, you can use the following
command:

.. code-block:: bash

    pytest --cov=src --cov-report=html --cov-report=html

The coverage report will be generated in the `htmlcov` directory, and you can open the `index.html` file in your web browser
to view the report.

Contributing Code
-----------------

If you want to contribute code to the project, please follow these guidelines:
1. Fork the repository and create a new branch for your feature or bug fix.
2. Write tests for your code and make sure they pass.
3. Make sure your code follows the project's coding style and conventions.
4. Submit a pull request with a clear description of your changes and why they are needed.
5. Be open to feedback and willing to make changes based on code reviews.
6. Ensure that your code is well-documented, including docstrings for functions and classes.
7. Update the documentation if your changes affect the usage or functionality of the package.
8. Keep your pull request focused on a single feature or bug fix to make it easier to review.
