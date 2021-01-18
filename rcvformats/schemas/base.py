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
        The version number of this schema

        :return: A string represting the version number
        """

    def validate_file(self, filename):
        """
        Opens the file and validates that it matches the expected schema

        :param filename: The JSON filename for the tabulated results
        :return: whether or not the validation failed
        """
        with open(filename, 'r') as file_obj:
            return self.validate_file_object(file_obj)

    @abc.abstractmethod
    def validate_file_object(self, file_object):
        """
        Same as func:`~validate_file` but accepts a file object instead of a filename
        """

    def last_error(self):
        """
        If validate() failed, this method will provide more detailed information
        on the error. The details vary by class type, though it will always be of type
        Exception

        :return: Exception with additional information on why the validation failed
        """
        assert self._last_error is None or isinstance(self._last_error, Exception)
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

    def validate_file_object(self, file_object):
        """ Opens the file and runs :func:`~validate_data` """
        try:
            data = json.load(file_object)
        except json.decoder.JSONDecodeError as error:
            self._last_error = error
            return False

        return self.validate_data(data)

    def validate_data(self, data):
        """
        Validates that the data matches the schema. If invalid, more data may be available
        by calling last_error()

        :param data: The input dictionary
        :return: Whether or not the data matches the schema
        """
        try:
            jsonschema.validate(data, self.schema)
            return True
        except jsonschema.exceptions.ValidationError as error:
            self._last_error = error
            return False
