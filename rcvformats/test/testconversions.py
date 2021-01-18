"""
Integration tests for conversions between file formats
"""

import json
import nose

from rcvformats.conversions import electionbuddy
from rcvformats.conversions import opavote


def _assert_conversion_correct(file_in, file_out, converter):
    """ Asserts that converter.parse(file_in) = file_out """
    converter.parse(file_in)
    actual_data = converter.to_universal_tabulator_format()
    with open(file_out, 'r') as file_obj:
        expected_data = json.load(file_obj)
    nose.tools.assert_dict_equal(actual_data, expected_data)


def test_electionbuddy_conversions_succeed():
    """ Converts electionbuddy CSV to standard format """
    filenames = [
        'testdata/electionbuddy-formats/standard.csv',
        'testdata/electionbuddy-formats/multiwinner.csv',
        'testdata/electionbuddy-formats/without-abstentions.csv'
    ]
    converter = electionbuddy.ElectionBuddyConverter()
    for filename in filenames:
        converter.parse(filename)
        converter.to_universal_tabulator_format()


def test_opavote_conversion_accurate():
    """ Converts opavote CSV to standard format """
    file_in = 'testdata/opavote-formats/fairvote.json'
    file_out = 'testdata/conversions/from-opavote.json'
    converter = opavote.OpavoteConverter()
    _assert_conversion_correct(file_in, file_out, converter)


def test_electionbuddy_conversion_accurate():
    """ Converts electionbuddy CSV to the standard format """
    file_in = 'testdata/electionbuddy-formats/standard.csv'
    file_out = 'testdata/conversions/from-electionbuddy.json'
    converter = electionbuddy.ElectionBuddyConverter()
    _assert_conversion_correct(file_in, file_out, converter)
