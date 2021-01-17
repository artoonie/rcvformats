"""
Validators for a given schema
"""

import json
import jsonschema


def validate(filename, schema):
    """
    Validates that the schema is respected
    :param filename: The JSON filename for the tabulated results
    :param schema: The schema data, as provided by schemas.py
    :raises jsonschema.exceptions.ValidationError' On any error
    """
    with open(filename, 'r') as file_object:
        data = json.load(file_object)
        jsonschema.validate(data, schema)
