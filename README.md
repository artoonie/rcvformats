![Python package](https://github.com/artoonie/rcvformats/workflows/Python%20package/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/rcvformats/badge/?version=latest)](https://rcvformats.readthedocs.io/en/latest/?badge=latest)

# RCV Formats
Build tools for the Ranked Choice Voting Ecosystem without having to support each file format individually. RCV Formats converts data from several sources into a single, standardized format with a command-line or python tooling.

#### Command-line

```bash
rcvformats convert -i <input-filename> -o <output-filename>
```

#### Python

```python
from rcvformats.conversions.automatic import AutomaticConverter

standardized_data = AutomaticConverter().convert_to_ut(input_filename)
```

The standardized format is the [Universal RCV Tabulator JSON](https://www.rcvresources.org/rcv-universal-tabulator). To understand this format, look at [examples](https://github.com/artoonie/rcvformats/tree/main/testdata/inputs/universal-tabulator) or [the jsonschema](https://github.com/artoonie/rcvformats/blob/main/rcvformats/jsonschemas/universaltabulator.schema.json).


## Installation
`pip3 install rcvformats`


## Additional Options
RCV Formats can also run schema validations and conversions from specific formats.

### Schema Validation
Validate that your file format matches one of several available schemas:

1. The Universal RCV Tabulator JSON format
2. The Opavote JSON format
3. The ElectionBuddy CSV format

Currently, validation is only on the structure of the data, not on its contents: it is possible for a validly-formatted file to still contain invalid data.

You can run the validation and examine errors with both python and bash:

#### Command-line

```bash
rcvformats validate -i <input-filename> -s <schema-type>
```

Valid schema validators on the command line are:
```bash
eb # for electionbuddy files
ov # for opavote files
ut # for universal tabulator files
```

#### Python

```python
from rcvformats.schemas import universaltabulator

schema = universaltabulator.SchemaV0()
is_valid = schema.validate('/path/to/file.json')

if not is_valid:
  print(schema.last_error())
```

Valid schema validators for python are:
```python
from rcvformats.schemas.electionbuddy import SchemaV0
from rcvformats.schemas.opavote import SchemaV1_0
from rcvformats.schemas.universaltabulator import SchemaV0
```

### File Format Conversion
You can convert from any of the supported formats and to the Universal RCV Tabulator format. The currently supported formats are:
1. ElectionBuddy CSVs
2. Opavote JSONs

You can run the conversion via:

#### Command-line

```bash
rcvformats convert -i <input-filename> -o <output-filename>
```

The bash script always uses the automatic converter.

#### Python

```python
from rcvformats.conversions import electionbuddy

converter = electionbuddy.ElectionBuddyConverter()
try:
  converter.convert_to_ut(filename)
except Exception as e:
  print("Errors: ", e)
```

Valid converters are:
```python
from rcvformats.converters.automatic import AutomaticConverter
from rcvformats.conversions.electionbuddy import ElectionBuddyConverter
from rcvformats.conversions.opavote import OpavoteConverter
```

The AutomaticConverter checks if the file matches any of the available schemas, and if it finds a matching schema, it runs the corresponding conversion (if a conversion is needed at all).

### Fill in missing "transfer" data
If you have a file format that does not have transfer data, and wish to generate it, you can use these tools.
Be careful: if you use batch elimination (more than one candidate eliminated in one round), the data will be fake and you should not rely on it.

#### Command-line

```bash
rcvformats transfer -i <input-filename> -o <output-filename>
```

#### Python

```python
from rcvformats.conversions.ut_without_transfers import UTWithoutTransfersConverter

converter = UTWithoutTransfersConverter()
try:
  converter.convert_to_ut(filename)
except Exception as e:
  print("Errors: ", e)
```

## Upcoming plans
1. Allow any format to be converted both to and from the Universal Tabulator format
2. More unit tests
3. Create both structure and data validations for the Universal Tabulator format
4. Validation for both tabulated formats and cast vote records

## Running test suite
Run `nosetests` in the root directory
