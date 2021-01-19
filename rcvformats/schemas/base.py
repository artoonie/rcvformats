"""
Loads supported schemas (currently only one: the Universal Tabulator schema)
"""

import abc
import json
import os

import jsonschema

from rcvformats.common import utils


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

    def validate(self, filename_or_fileobj):
        """
        Validates that the file matches the expected schema

        :param filename_or_fileobj: The JSON filename or file object for the tabulated results
        :return: whether or not the validation failed
        """
        if utils.is_file_obj(filename_or_fileobj):
            return self._validate_file_object(filename_or_fileobj)
        if utils.is_filename(filename_or_fileobj):
            with open(filename_or_fileobj, 'r') as file_object:
                return self._validate_file_object(file_object)
        # Couldn't open the file at all
        self._last_error = TypeError("Couldn't open file")
        return False

    @abc.abstractmethod
    def _validate_file_object(self, file_object):
        """
        Implements the bulk of func:`~validate`
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
        filepath = os.path.join(self._get_jsonschema_directory(), filename)
        with open(filepath, 'r') as file_object:
            self.schema = json.load(file_object)

        super().__init__()

    @classmethod
    def _get_jsonschema_directory(cls):
        return os.path.join(os.path.dirname(__file__), '..', 'jsonschemas')

    def _validate_file_object(self, file_object):
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
