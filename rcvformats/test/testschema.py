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
    with open(json_filename, 'r+', encoding='utf-8') as file_obj:
        data = json.load(file_obj)
        modifier_func(data)

    # Write it to a tempfile
    modified_json_tempfile = tempfile.NamedTemporaryFile()  # pylint: disable=consider-using-with
    with open(modified_json_tempfile.name, 'w', encoding='utf-8') as file_obj:
        json.dump(data, file_obj)
    return modified_json_tempfile


def test_universal_tabulator_formats_valid():
    """ Verifies that the example formats are valid """
    schema = universaltabulator.SchemaV0()
    _validate_files_in_dir_with('testdata/inputs/universal-tabulator', schema)


def test_opavote_v10_formats_valid():
    """ Verifies that the opavote pre-2022 formats work """
    schema = opavote.SchemaV1_0()
    _validate_files_in_dir_with('testdata/inputs/opavote10', schema)


def test_opavote_v11_formats_valid():
    """ Verifies that the opavote post-2022 formats work """
    schema = opavote.SchemaV1_1()
    _validate_files_in_dir_with('testdata/inputs/opavote11', schema)


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


def test_threshold_is_optional():
    """ Verifies that threshold may be nonexistent """
    badjson_tempfile = _modify_json_with('testdata/inputs/universal-tabulator/one-round.json',
                                         lambda d: d['config'].pop('threshold'))
    schema = universaltabulator.SchemaV0()
    assert schema.validate(badjson_tempfile.name)


def test_can_pass_raw_json():
    """
    Verifies that raw JSON data can be passed:
    filelike objects or filenames are not mandatory
    """
    filename = 'testdata/inputs/universal-tabulator/one-round.json'
    with open(filename, 'r', encoding='utf-8') as fileobj:
        data = json.load(fileobj)
    schema = universaltabulator.SchemaV0()
    assert schema.validate(data)
