# es-cli

## how to build and run application in dev
- `pip install virtualenv`
- `virtualenv venv` to create virtual environment
- `source ./venv/bin/activate` activate virtual env.
- `cd` into project folder.
- `pip install --editable .` will install all dependencies in `setup.py`.
- use wake word `escli` to launch the cli.

## how to run tests
- `pip install -r requirements.txt`
- run `pytest`