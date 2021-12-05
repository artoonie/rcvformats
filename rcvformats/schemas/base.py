"""
Loads supported schemas (currently only one: the Universal Tabulator schema)
"""

import abc
import json
import os

import jsonschema

from rcvformats.common import utils


class DataError(Exception):
    """ An error raised if the schema is correct, but the data inside it is invalid """


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

    def validate(self, data):
        """
        Validates that the file matches the expected schema

        :param data: The JSON filename, file object, or JSON data for the tabulated results
        :return: whether or not the validation failed
        """
        if utils.is_file_obj(data):
            return self._validate_data(data)
        if isinstance(data, dict):
            return self._validate_data(data)
        if utils.is_filename(data):
            with open(data, 'rb') as file_object:
                return self._validate_data(file_object)

        # Couldn't open the file at all
        self._last_error = TypeError("Couldn't open file")
        return False

    @abc.abstractmethod
    def _validate_data(self, data):
        """
        Implements the bulk of func:`~validate`
        Should accept either a filelike object or raw, loaded data
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
        with open(filepath, 'r', encoding='utf-8') as file_object:
            self.schema = json.load(file_object)

        super().__init__()

    @classmethod
    def _get_jsonschema_directory(cls):
        return os.path.join(os.path.dirname(__file__), '..', 'jsonschemas')

    def _validate_data(self, data):
        """
        Opens the file and runs :func:`~is_schema_valid`
        if is_filelike, opens the file, otherwise, the data should be a python dictionary
        """
        if not isinstance(data, dict):
            try:
                file_bytes = data.read()
                data = json.loads(file_bytes)
            except (json.decoder.JSONDecodeError, UnicodeDecodeError) as error:
                self._last_error = error
                return False

        return self.validate_schema_and_logic(data)

    def validate_schema_and_logic(self, data):
        """ Runs both the schema and logic check """
        if not self.is_schema_valid(data):
            return False

        if not self.is_data_valid(data):
            return False

        return True

    def is_schema_valid(self, data):
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

    def is_data_valid(self, data):
        """
        Additional validations to ensure the data is correct.

        :param data: The input dictionary, which must match the schema
        :return: Whether or not the data is acceptable
        """
        try:
            self.ensure_data_is_logical(data)
            return True
        except DataError as error:
            self._last_error = error
            return False

    def ensure_data_is_logical(self, data):
        """
        Override to add any additional data validations you need done.
        Raise an exception if anything is invalid
        """
