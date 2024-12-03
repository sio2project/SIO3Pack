# SIO3Pack


## Development

### Test without django support

Install the package in editable mode and make sure that `django` and 
`pytest-django` are not installed.

```bash
pip install -e .[tests]
pip uninstall django pytest-django
```

Then follow the instructions in 
[General testing information](#general-testing-information).


### Test with django support

Install the package in editable mode and with django dependencies:

```bash
pip install -e .[django,tests,django_tests]
```

Then follow the instructions in 
[General testing information](#general-testing-information).


### General testing information

Run the tests with `pytest` in the root directory of 
the repository.

```bash
pytest -v
```

To run tests in parallel, use the following command.

```bash
pytest -v -n auto
```

To run tests with coverage, use the following command.

```bash
pytest -v --cov=sio3pack --cov-report=html
```

Coverage report will be generated in the `htmlcov/index.html`.
