import os
import json

root = os.path.dirname(__file__)
literal_file = os.path.join(root, "esliterals.json")

with open(literal_file) as f:
    literals = json.load(f)


def get_literals(literal_type):
    # Where `literal_type` is one of 'keywords', 'functions', 'datatypes',
    # returns a list of literal values of that type.

    return literals[literal_type]
