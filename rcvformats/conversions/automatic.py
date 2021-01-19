"""
Attempts to convert any file to the standard format.
If you know the file format, you should not use this - it will
loop through all schemas which will be needlessly slow.
"""

import json

from rcvformats.conversions.base import CouldNotConvertException
from rcvformats.conversions.electionbuddy import ElectionBuddyConverter
from rcvformats.conversions.opavote import OpavoteConverter
from rcvformats.schemas.electionbuddy import SchemaV0 as ElectionBuddySchema
from rcvformats.schemas.opavote import SchemaV1_0 as OpavoteSchema
from rcvformats.conversions.base import Converter


class AutomaticConverter(Converter):
    """ Interface for converters """

    def __init__(self):
        # In order of likelihood of a hit - just my guess
        self.additional_schemas = [
            (ElectionBuddySchema(), ElectionBuddyConverter),
            (OpavoteSchema(), OpavoteConverter)
        ]

        super().__init__()

    def _convert_file_object_to_ut(self, file_object):
        # If it matches the schema already, load and return the data
        if self.ut_schema.validate(file_object):
            file_object.seek(0)
            return json.load(file_object)

        # Otherwise, loop through each schema, and if it matches, run the converter
        for schema, converter in self.additional_schemas:
            file_object.seek(0)
            matches_schema = schema.validate(file_object)
            if matches_schema:
                file_object.seek(0)
                return converter().convert_to_ut(file_object)

        # If it failed, accumulate all errors from schemas
        err = CouldNotConvertException("Could not find a compatible parser")
        err.args += (self.ut_schema.last_error(),)
        for schema, _ in self.additional_schemas:
            err.args += (schema.last_error(),)
        raise err
