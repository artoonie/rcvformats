from rcvformats import schemas
from rcvformats import validate

def test_multiwinner_valid():
    multiwinner_filename = 'testdata/universal-tabulator-formats/macomb-multiwinner.json'
    schema = schemas.latest_universal_tabulator_schema()
    validator = validate.Validator()
    validator.validate(multiwinner_filename, schema)
