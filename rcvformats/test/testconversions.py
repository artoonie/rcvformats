"""
Tests all conversions from other file formats to the tabulator
"""

from rcvformats.conversions import from_electionbuddy as electionbuddy


def test_schemas():
    """ Loads electionbuddy CSVs """
    filenames = [
        'testdata/electionbuddy-formats/standard.csv',
        'testdata/electionbuddy-formats/multiwinner.csv',
        'testdata/electionbuddy-formats/without-abstentions.csv'
    ]
    converter = electionbuddy.CSVReader()
    for filename in filenames:
        converter.parse(filename)
        output = converter.to_universal_tabulator_format()
