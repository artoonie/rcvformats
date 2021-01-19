"""
Tests that our example JSONs all pass validation
"""

import os

from rcvformats.schemas import electionbuddy
from rcvformats.schemas import universaltabulator
from rcvformats.schemas import opavote


def _validate_files_in_dir_with(directory, schema):
    for filename in os.listdir(directory):
        if not schema.validate(os.path.join(directory, filename)):
            raise schema.last_error()


def test_universal_tabulator_formats_valid():
    """ Verifies that the example formats are valid """
    schema = universaltabulator.SchemaV0()
    _validate_files_in_dir_with('testdata/inputs/universal-tabulator', schema)


def test_opavote_formats_valid():
    """ Verifies that the example formats are valid """
    schema = opavote.SchemaV1_0()
    _validate_files_in_dir_with('testdata/inputs/opavote', schema)


def test_electionbuddy_formats_valid():
    """ Verifies that the example formats are valid """
    schema = electionbuddy.SchemaV0()
    _validate_files_in_dir_with('testdata/inputs/electionbuddy', schema)
