"""
Tests that our example JSONs all pass validation
"""

from rcvformats import schemas


def test_universal_tabulator_formats_valid():
    """ Verifies that the multiwinner format is valid """
    filenames = [
        'testdata/universal-tabulator-formats/macomb-multiwinner.json',
        'testdata/universal-tabulator-formats/one-round.json',
        'testdata/universal-tabulator-formats/simple.json'
    ]
    schema = schemas.UniversalTabulatorSchemaV0()
    for filename in filenames:
        schema.validate(filename)
