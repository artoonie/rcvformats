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
from rcvformats.conversions.ut_without_transfers import UTWithoutTransfersConverter
from rcvformats.conversions.base import Converter


class AutomaticConverter(Converter):
    """ Interface for converters """

    def __init__(self):
        # In order of likelihood of a hit - just my guess.
        # As this list grows, we should really consider doing something intelligent.
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
        additional_errors = []
        for converterType in self.converters:
            file_object.seek(0)
            try:
                data = converterType().convert_to_ut(file_object)
                converter = UTWithoutTransfersConverter(allow_guessing=False)
                return converter.fill_in_tally_data(data)
            except CouldNotConvertException as exception:
                additional_errors.append(converterType.__name__ + ":" + str(exception))
                continue

        # If it failed, accumulate all errors from schemas
        error_message = "When trying to parse as the Universal Tabulator schema, " +\
            f"received error: \"{str(self.ut_schema.last_error())}\". " +\
            "Further, it did not match any other known format. Additional errors: \n\n" +\
            '\n\n'.join(additional_errors)
        raise CouldNotConvertException(error_message)
