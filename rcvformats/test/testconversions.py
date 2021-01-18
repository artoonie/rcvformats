"""
Integration tests for conversions between file formats
"""

import json
import nose

from rcvformats.conversions import electionbuddy
from rcvformats.conversions import opavote


def _assert_conversion_correct(file_in, file_out, converter):
    """ Asserts that converter.convert_to_ut(file_in) = file_out """
    actual_data = converter.convert_to_ut_and_validate(file_in)
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
        converter.convert_to_ut_and_validate(filename)


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
