"""
Loads supported schemas (currently only one: the Universal Tabulator schema)
"""

import json


def latest_universal_tabulator_schema():
    """
    Loads the latest Universal RCV Tabulator schema.
    Pass the result of this function into the Validator.
    """
    filename = 'rcvformats/schemas/universaltabulator.schema.json'
    with open(filename, 'r') as file_object:
        schema = json.load(file_object)
    return schema
