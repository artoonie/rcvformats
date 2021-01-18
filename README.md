# RCV Formats
A collection of parsers and converters from various RCV formats to the standard [Universal RCV Tabulator format](https://www.rankedchoicevoting.org/universal_rcv_tabulator).

## Validation
The following schemas can be validated. Currently, validation does not guarantee they can be imported: the validators make no sanity checks to ensure the math works out, or that there are no typos in candidate names. Rather, they only validate the structure.

1. The Universal RCV Tabulator format
1. The Opavote format

You can run the validation and examine errors via:
```python
from rcvformats.schemas import universaltabulator

schema = universaltabulator.SchemaV0()
is_valid = schema.validate_file('/path/to/file.json')

if not is_valid:
  print(schema.get_last_error())
```

Valid schema validators are:
```python
from rcvformats.schemas.universaltabulator import SchemaV0
from rcvformats.schemas.opavote import SchemaV1_0
```

## Conversion
You can convert from any of the supported formats and to the Universal RCV Tabulator format. The currently supported formats are:
1. ElectionBuddy CSVs
1. Opavote JSONs

You can run the conversion via:

```python
from rcvformats.conversions import electionbuddy

converter = electionbuddy.ElectionBuddyConverter()
try:
  converter.parse(filename)
  converter.to_universal_tabulator_format()
except Exception as e:
  print("Errors: ", e)
```

Valid converters are:
```python
from rcvformats.conversions.electionbuddy import ElectionBuddyConverter
from rcvformats.conversions.opavote import OpavoteConverter
```

## Upcoming plans
1. Allow any format to be converted both to and from the Universal Tabulator format
2. Implement schema validation and migration for the ElectionBuddy CSV
3. More unit tests
4. Create both structure and data validations for the Universal Tabulator format

## Running test suite
Just run `nosetests` in the root directory
