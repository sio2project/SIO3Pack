from sio3pack.graph import GraphOperation

# SIO3Pack

## Prerequisites
```
- Python 3.9 or higher
- pip
- Linux or macOS operating system
- Django 4.2.x (for Django support)
```

## Instalation
```
pip install sio3pack
```
## Example usage (in python)

### In OIOIOI

```python
# Package unpacking
import sio3pack, sio3workers
from django.conf import settings

package = sio3pack.from_file(path_to_package, django_settings=settings)
graph_op: GraphOperation = package.get_unpack_operation()
results = sioworkers.run(graph_op)
graph_op.return_results(results)
package.save_to_db(problem_id=1)
```

### Locally (for example `sinol-make`)

```python
import sio3pack, sio3workers.local

package = sio3pack.from_file(path_to_package)
graph_op: GraphOperation = package.get_unpack_operation()
results = sio3workers.local.run(graph_op)
graph_op.return_results(results)
```

---

## Development

### Test without django support

Install the package in editable mode and make sure that `django` and 
`pytest-django` are not installed.

```bash
pip install -e ".[tests]"
pip uninstall django pytest-django
```

Then follow the instructions in 
[General testing information](#general-testing-information).


### Test with django support

Install the package in editable mode along with Django dependencies:

```bash
pip install -e ".[django,tests,django_tests]"
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

To run coverage tests, use the following command.

```bash
pytest -v --cov=sio3pack --cov-report=html
```

The coverage report will be generated in the file `htmlcov/index.html`.
