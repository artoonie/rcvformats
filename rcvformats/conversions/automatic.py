"""
Attempts to convert any file to the standard format.
If you know the file format, you should not use this - it will
loop through all schemas which will be needlessly slow.
"""

import json

from rcvformats.conversions.base import CouldNotConvertException
from rcvformats.conversions.dominion import DominionConverter
from rcvformats.conversions.electionbuddy import ElectionBuddyConverter
from rcvformats.conversions.opavote import OpavoteConverter
from rcvformats.conversions.base import Converter


class AutomaticConverter(Converter):
    """ Interface for converters """

    def __init__(self):
        # In order of likelihood of a hit - just my guess
        self.converters = [
            DominionConverter,
            ElectionBuddyConverter,
            OpavoteConverter
        ]

        super().__init__()

    def _convert_file_object_to_ut(self, file_object):
        # If it matches the schema already, load and return the data
        if self.ut_schema.validate(file_object):
            file_object.seek(0)
            return json.load(file_object)

        # Otherwise, try each converter - skipping schemas for speed
        for converter in self.converters:
            file_object.seek(0)
            try:
                return converter().convert_to_ut(file_object)
            except CouldNotConvertException:
                continue

        # If it failed, accumulate all errors from schemas
        error_message = "When trying to parse as the Universal Tabulator schema, " +\
                        f"received error: \"{str(self.ut_schema.last_error())}\". " +\
            "Further, it did not match any other known format."
        raise CouldNotConvertException(error_message)
