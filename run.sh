#!/bin/bash

# Ensure the virtual environment is activated
DIR="$(dirname "$0")"
"$DIR/.venv/bin/python" "-m pip install pyside6"
"$DIR/.venv/bin/python" "$DIR/main.py"

