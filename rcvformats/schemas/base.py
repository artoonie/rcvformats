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
    def validate_file(self, filename):
        """
        Opens the file and validates that it matches the expected schema
        :param filename: The JSON filename for the tabulated results
        :return: whether or not the validation failed
        """

    @abc.abstractmethod
    def validate_data(self, data):
        """
        Reads the data and validates that it matches the expected schema
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


class GenericJsonSchema(Schema):
    """ Base class for a JSON Schema """
    @property
    @abc.abstractmethod
    def schema_filename(self):
        """ The JSON Schema filename """

    def __init__(self):
        filename = self.schema_filename
        with open(filename, 'r') as file_object:
            self.schema = json.load(file_object)

        super().__init__()

    def validate_file(self, filename):
        try:
            with open(filename, 'r') as file_object:
                data = json.load(file_object)
        except json.decoder.JSONDecodeError as error:
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
