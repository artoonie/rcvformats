"""
Loads supported schemas (currently only one: the Universal Tabulator schema)
"""

import abc
import json
import jsonschema


class Schema(abc.ABC):
    """
    A single version of a single schema
    """

    def __init__(self):
        self._last_error = None

    @abc.abstractmethod
    def version(self):
        """
        Which version number
        :return: A string represting the version number
        """

    @abc.abstractmethod
    def validate(self, filename):
        """
        Which version number
        :param filename: The JSON filename for the tabulated results
        :return: whether or not the validation failed
        """

    def last_error(self):
        """
        If validate() failed, this method will provide more detailed information
        on the error. The details vary by class type.
        :return: Additional information on why the validation failed
        """
        return self._last_error


class UniversalTabulatorSchemaV0(Schema):
    """ Schema for the initial version of the Universal RCV Tabulator """

    def __init__(self):
        filename = 'rcvformats/schemas/universaltabulator.schema.json'
        with open(filename, 'r') as file_object:
            self.schema = json.load(file_object)

        super().__init__()

    def version(self):
        return "Unversioned:V0"

    def validate(self, filename):
        with open(filename, 'r') as file_object:
            data = json.load(file_object)

        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.exceptions.ValidationError as error:
            self._last_error = error
            return False
