"""
Tests that our example JSONs all pass validation
"""

from rcvformats import schemas
from rcvformats import validate


def test_multiwinner_valid():
    """ Verifies that the multiwinner format is valid """
    multiwinner_filename = 'testdata/universal-tabulator-formats/macomb-multiwinner.json'
    schema = schemas.latest_universal_tabulator_schema()
    validate.validate(multiwinner_filename, schema)
