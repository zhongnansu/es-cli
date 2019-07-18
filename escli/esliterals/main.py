"""
Load file "esliterals.json" with literal type of "keywords" and "functions", which
is supported by Open Distro SQL Plugin.
"""
import os
import json

root = os.path.dirname(__file__)
literal_file = os.path.join(root, "esliterals.json")

with open(literal_file) as f:
    literals = json.load(f)


def get_literals(literal_type):
    """Return a list of literal values of certain literal type."""
    return literals[literal_type]
