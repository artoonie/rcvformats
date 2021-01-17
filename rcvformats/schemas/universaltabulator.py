"""
Loads supported schemas (currently only one: the Universal Tabulator schema)
"""

import json
import jsonschema

from rcvformats.schemas.base import Schema


class SchemaV0(Schema):
    """ Schema for the initial version of the Universal RCV Tabulator """

    def __init__(self):
        filename = 'rcvformats/jsonschemas/universaltabulator.schema.json'
        with open(filename, 'r') as file_object:
            self.schema = json.load(file_object)

        super().__init__()

    def version(self):
        return "Unversioned:V0"

    def validate_file(self, filename):
        try:
            with open(filename, 'r') as file_object:
                data = json.load(file_object)
        except json.JsonValidationError as error:
            self._last_error = error
            return False

        return self.validate_data(data)

    def validate_data(self, data):
        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.exceptions.ValidationError as error:
            self._last_error = error
            return False
