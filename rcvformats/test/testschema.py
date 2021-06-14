"""
Tests that our example JSONs all pass validation
"""

import json
import tempfile
import os

from rcvformats.schemas import electionbuddy
from rcvformats.schemas import universaltabulator
from rcvformats.schemas import opavote


def _validate_files_in_dir_with(directory, schema):
    for filename in os.listdir(directory):
        if not schema.validate(os.path.join(directory, filename)):
            raise schema.last_error()


def _modify_json_with(json_filename, modifier_func):
    """
    Given a modifier_func which modifies the data in the given file,
    updates the json file and returns a Tempfile holding the new data
    """
    # Update the sidecar data
    with open(json_filename, 'r+') as file_obj:
        data = json.load(file_obj)
        modifier_func(data)

    # Write it to a tempfile
    modified_json_tempfile = tempfile.NamedTemporaryFile()
    with open(modified_json_tempfile.name, 'w') as file_obj:
        json.dump(data, file_obj)
    return modified_json_tempfile


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


def test_empty_threshold_not_valid():
    """ (Regression) Verifies that empty string is not valid for threshold """
    badjson_tempfile = _modify_json_with('testdata/inputs/universal-tabulator/one-round.json',
                                         lambda d: d['config'].update({'threshold': ''}))
    schema = universaltabulator.SchemaV0()
    assert not schema.validate(badjson_tempfile.name)


def test_threshold_is_required():
    """ Verifies that threshold must exist """
    badjson_tempfile = _modify_json_with('testdata/inputs/universal-tabulator/one-round.json',
                                         lambda d: d['config'].pop('threshold'))
    schema = universaltabulator.SchemaV0()
    assert not schema.validate(badjson_tempfile.name)
