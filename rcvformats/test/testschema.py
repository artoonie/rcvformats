"""
Tests that our example JSONs all pass validation
"""

from rcvformats.schemas import universaltabulator
from rcvformats.schemas import opavote


def test_universal_tabulator_formats_valid():
    """ Verifies that the example formats are valid """
    filenames = [
        'testdata/universal-tabulator-formats/macomb-multiwinner.json',
        'testdata/universal-tabulator-formats/one-round.json',
        'testdata/universal-tabulator-formats/simple.json'
    ]
    schema = universaltabulator.SchemaV0()
    for filename in filenames:
        assert schema.validate_file(filename)


def test_opavote_formats_valid():
    """ Verifies that the example formats are valid """
    filename = 'testdata/opavote-formats/fairvote.json'
    schema = opavote.SchemaV1_0()
    assert schema.validate_file(filename)
