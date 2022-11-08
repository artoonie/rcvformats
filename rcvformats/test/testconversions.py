"""
Integration tests for conversions between file formats
"""

import os
import json
import nose

from rcvformats.conversions import automatic
from rcvformats.conversions import dominion_multi_converter
from rcvformats.conversions import dominion
from rcvformats.conversions import electionbuddy
from rcvformats.conversions import opavote
from rcvformats.conversions.ut_without_transfers import UTWithoutTransfersConverter
from rcvformats.schemas import universaltabulator


def _assert_conversion_correct(file_in, file_out, converter):
    """ Asserts that converter.convert_to_ut(file_in) = file_out """
    nose.tools.assert_dict_equal.__self__.maxDiff = None
    actual_data = converter.convert_to_ut_and_validate(file_in)
    with open(file_out, 'r', encoding='utf-8') as file_obj:
        expected_data = json.load(file_obj)
    nose.tools.assert_dict_equal(actual_data, expected_data)


def _files_in_dir(input_dir):
    """ Yields all CSV and json files in dir """
    for filename in os.listdir(input_dir):
        if not filename.endswith('.json') and \
                not filename.endswith('.csv') and \
                not filename.endswith('.xlsx'):
            continue
        yield filename


def _assert_auto_gives_same_result_as(input_dir, direct_converter):
    """
    Asserts that the AutomaticConverter creates the same results as the provided one
    for every file in the provided directory, plus a transfer dict
    """
    auto_converter = automatic.AutomaticConverter()
    add_transfer_converter = UTWithoutTransfersConverter(allow_guessing=False)

    for filename in _files_in_dir(input_dir):
        filepath = os.path.join(input_dir, filename)
        auto_data = auto_converter.convert_to_ut_and_validate(filepath)
        expected_data_without_xfer = direct_converter.convert_to_ut_and_validate(filepath)
        expected_data = add_transfer_converter.fill_in_tally_data(expected_data_without_xfer)

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


def test_opavote_v10_conversion_accurate():
    """ Converts opavote JSON to standard format """
    file_in = 'testdata/inputs/opavote10/fairvote.json'
    file_out = 'testdata/conversions/from-opavote-v10.json'
    converter = opavote.OpavoteConverter()
    _assert_conversion_correct(file_in, file_out, converter)


def test_opavote_v11_conversion_accurate():
    """ Converts opavote JSON to standard format """
    file_in = 'testdata/inputs/opavote11/2022-example.json'
    file_out = 'testdata/conversions/from-opavote-v11.json'
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


def test_dominion_conversion_accurate():
    """ Converts dominion XLSX to the standard format """
    file_in = 'testdata/inputs/dominion/las-cruces-mayor.xlsx'
    file_out = 'testdata/conversions/from-dominion.json'
    converter = dominion.DominionConverter()
    _assert_conversion_correct(file_in, file_out, converter)


def test_automatic_conversions_universal_tabulator():
    """ Tests that the automatic conversion works when given Universal Tabulator data """
    converter = automatic.AutomaticConverter()
    input_dir = 'testdata/inputs/universal-tabulator'

    for filename in _files_in_dir(input_dir):
        filepath = os.path.join(input_dir, filename)
        output_data = converter.convert_to_ut_and_validate(filepath)

        # Must be unchanged
        with open(filepath, 'r', encoding='utf-8') as input_file:
            input_data = json.load(input_file)

        nose.tools.assert_dict_equal(input_data, output_data)


def test_automatic_conversions_opavote10():
    """ Tests that the automatic conversion works when given Opavote V1.0 data """
    converter = opavote.OpavoteConverter()
    input_dir = 'testdata/inputs/opavote10'
    _assert_auto_gives_same_result_as(input_dir, converter)


def test_automatic_conversions_opavote11():
    """ Tests that the automatic conversion works when given Opavote V1.1 data """
    converter = opavote.OpavoteConverter()
    input_dir = 'testdata/inputs/opavote11'
    _assert_auto_gives_same_result_as(input_dir, converter)


def test_automatic_conversions_dominion():
    """ Tests that the automatic conversion works when given Dominion data """
    converter = dominion.DominionConverter()
    input_dir = 'testdata/inputs/dominion'
    _assert_auto_gives_same_result_as(input_dir, converter)


def test_automatic_conversions_electionbuddy():
    """ Tests that the automatic conversion works when given ElectionBuddy data """
    converter = electionbuddy.ElectionBuddyConverter()
    input_dir = 'testdata/inputs/electionbuddy'
    _assert_auto_gives_same_result_as(input_dir, converter)


def _does_all_single_elim_have_transfer_data(data):
    for result in data['results']:
        tally_results = result['tallyResults']
        if len(tally_results) != 1:
            continue

        tally_result = tally_results[0]
        if 'elected' in tally_result:
            continue

        if not tally_result['transfers']:
            return False
    return True


def _does_all_batch_elim_have_transfer_data(data):
    for result in data['results']:
        tally_results = result['tallyResults']
        if len(tally_results) == 1:
            continue

        for tally_result in tally_results:
            if 'elected' in tally_result:
                continue
            if not tally_result['transfers']:
                return False
    return True


def test_add_xfer_without_fake_data():
    """ Tests allow_guessing=False in UT Without Transfers """
    converter = UTWithoutTransfersConverter(allow_guessing=False)
    input_filename = 'testdata/inputs/ut-without-transfers/nyc-batch-elim.json'
    with_transfers = converter.convert_to_ut(input_filename)
    assert _does_all_single_elim_have_transfer_data(with_transfers)
    assert not _does_all_batch_elim_have_transfer_data(with_transfers)


def test_add_xfer_with_fake_data():
    """ Tests allow_guessing=True in UT Without Transfers """
    converter = UTWithoutTransfersConverter(allow_guessing=True)
    input_filename = 'testdata/inputs/ut-without-transfers/nyc-batch-elim.json'
    with_transfers = converter.convert_to_ut(input_filename)
    assert _does_all_single_elim_have_transfer_data(with_transfers)
    assert _does_all_batch_elim_have_transfer_data(with_transfers)


def test_add_xfer_accepts_json():
    """ Tests that raw JSON data can be passed in """
    converter = UTWithoutTransfersConverter(allow_guessing=False)
    input_filename = 'testdata/inputs/ut-without-transfers/nyc-batch-elim.json'
    with open(input_filename, 'r', encoding='utf-8') as file_obj:
        data = json.load(file_obj)
        with_transfers = converter.convert_to_ut(data)
    assert _does_all_single_elim_have_transfer_data(with_transfers)
    assert not _does_all_batch_elim_have_transfer_data(with_transfers)


def test_explode_multi_format():
    """ Test the single Dominion XML turns into 25 RCTab JSONs """
    converter = dominion_multi_converter.DominionMultiConverter()
    input_filename = 'testdata/inputs/dominion-multi-converter.xml'
    with open(input_filename, 'r', encoding='utf-8') as file_obj:
        results = converter.explode_to_files(file_obj)

    # There are 25 contests, and they are all valid schemas
    assert len(results) == 25
    schema = universaltabulator.SchemaV0()
    for named_temp_file in results.values():
        if not schema.validate(named_temp_file.name):
            raise schema.last_error()
