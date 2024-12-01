#!/bin/bash

cd "`dirname $0`"

cd tests/test_django
./manage.py makemigrations
./manage.py migrate
cd ../..

if [ -z "$1" ]; then
  pytest -v tests/
else
  pytest -v tests/ $1
fi
