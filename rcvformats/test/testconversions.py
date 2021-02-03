"""
Integration tests for conversions between file formats
"""

import os
import json
import nose

from rcvformats.conversions import automatic
from rcvformats.conversions import electionbuddy
from rcvformats.conversions import opavote


def _assert_conversion_correct(file_in, file_out, converter):
    """ Asserts that converter.convert_to_ut(file_in) = file_out """
    nose.tools.assert_dict_equal.__self__.maxDiff = None
    actual_data = converter.convert_to_ut_and_validate(file_in)
    with open(file_out, 'r') as file_obj:
        expected_data = json.load(file_obj)
    nose.tools.assert_dict_equal(actual_data, expected_data)


def _files_in_dir(input_dir):
    """ Yields all CSV and json files in dir """
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json') and not filename.endswith('.csv'):
            continue
        yield filename


def _assert_auto_gives_same_result_as(input_dir, direct_converter):
    """
    Asserts that the AutomaticConverter creates the same results as the provided one
    for every file in the provided directory
    """
    auto_converter = automatic.AutomaticConverter()

    for filename in _files_in_dir(input_dir):
        filepath = os.path.join(input_dir, filename)
        auto_data = auto_converter.convert_to_ut_and_validate(filepath)
        expected_data = direct_converter.convert_to_ut_and_validate(filepath)

        nose.tools.assert_dict_equal(auto_data, expected_data)


def test_electionbuddy_conversions_succeed():
    """ Converts electionbuddy CSV to standard format """
    filenames = [
        'testdata/inputs/electionbuddy/standard.csv',
        'testdata/inputs/electionbuddy/multiwinner.csv',
        'testdata/inputs/electionbuddy/without-abstentions.csv'
    ]
    converter = electionbuddy.ElectionBuddyConverter()
    for filename in filenames:
        converter.convert_to_ut_and_validate(filename)


def test_opavote_conversion_accurate():
    """ Converts opavote JSON to standard format """
    file_in = 'testdata/inputs/opavote/fairvote.json'
    file_out = 'testdata/conversions/from-opavote.json'
    converter = opavote.OpavoteConverter()
    _assert_conversion_correct(file_in, file_out, converter)


def test_electionbuddy_conversion_accurate():
    """ Converts electionbuddy CSV to the standard format """
    file_in = 'testdata/inputs/electionbuddy/standard.csv'
    file_out = 'testdata/conversions/from-electionbuddy.json'
    converter = electionbuddy.ElectionBuddyConverter()
    _assert_conversion_correct(file_in, file_out, converter)

    file_in = 'testdata/inputs/electionbuddy/standard-with-threshold.csv'
    file_out = 'testdata/conversions/from-electionbuddy-with-threshold.json'
    converter = electionbuddy.ElectionBuddyConverter()
    _assert_conversion_correct(file_in, file_out, converter)


def test_automatic_conversions_universal_tabulator():
    """ Tests that the automatic conversion works when given Universal Tabulator data """
    converter = automatic.AutomaticConverter()
    input_dir = 'testdata/inputs/universal-tabulator'

    for filename in _files_in_dir(input_dir):
        filepath = os.path.join(input_dir, filename)
        output_data = converter.convert_to_ut_and_validate(filepath)

        # Must be unchanged
        with open(filepath, 'r') as input_file:
            input_data = json.load(input_file)

        nose.tools.assert_dict_equal(input_data, output_data)


def test_automatic_conversions_opavote():
    """ Tests that the automatic conversion works when given Opavote data """
    converter = opavote.OpavoteConverter()
    input_dir = 'testdata/inputs/opavote'
    _assert_auto_gives_same_result_as(input_dir, converter)


def test_automatic_conversions_electionbuddy():
    """ Tests that the automatic conversion works when given ElectionBuddy data """
    converter = electionbuddy.ElectionBuddyConverter()
    input_dir = 'testdata/inputs/electionbuddy'
    _assert_auto_gives_same_result_as(input_dir, converter)
