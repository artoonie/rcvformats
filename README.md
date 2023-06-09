![Python package](https://github.com/artoonie/rcvformats/workflows/Python%20package/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/rcvformats/badge/?version=latest)](https://rcvformats.readthedocs.io/en/latest/?badge=latest)

# RCV Formats
RCV Formats helps programmers and researchers build tools that analyze the results of a Ranked-Choice Voting election without having to support the many file formats used to report RCV results.

RCV Formats converts data from several sources into a standardized format. It supports both python and command-line tools

Currently supported input formats are:
1. The Universal RCV Tabulator JSON format
2. The Opavote JSON format
3. The ElectionBuddy CSV format
4. The Dominion XLSX format
5. The Dominion TXT format

As well as the Dominion first-round-only XML format (used in Alaska), which contains the first rounds of several elections. All other converters contain the results of just one election per file.

The standardized output format is the [Universal RCV Tabulator JSON](https://www.rcvresources.org/rcv-universal-tabulator). To understand this format, look at [examples](https://github.com/artoonie/rcvformats/tree/main/testdata/inputs/universal-tabulator) or [the jsonschema](https://github.com/artoonie/rcvformats/blob/main/rcvformats/jsonschemas/universaltabulator.schema.json).

## Demo

#### Command-line

```bash
rcvformats convert -i <input-filename> -o <output-filename>
```

#### Python

```python
from rcvformats.conversions.automatic import AutomaticConverter

standardized_data = AutomaticConverter().convert_to_ut(input_filename)
```


## Installation
Install the library via pip:

`pip3 install rcvformats`

## Convert to Standardized Format
You can convert from any of the supported formats.
Use this functionality to support a wide array of input data while only writing code to support a single format.

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
from rcvformats.conversions.dominion_txt import DominionTxtConverter
from rcvformats.conversions.dominion_xlsx import DominionXlsxConverter
from rcvformats.conversions.electionbuddy import ElectionBuddyConverter
from rcvformats.conversions.opavote import OpavoteConverter
```

The AutomaticConverter checks if the file matches any of the available schemas, and if it finds a matching schema, it runs the corresponding conversion (if a conversion is needed at all).


## Schema Validation
Validate that your file is supported by RCVFormats.

Validation is only on the structure of the data, not on its contents: it is possible for a validly-formatted file to still contain invalid data.

#### Command-line

```bash
rcvformats validate -i <input-filename> -s <schema-type>
```

Valid schema validators on the command line are 'eb' (for electionbuddy files), `ov10` (for opavote files pre-2022), `ov11` (for opavote files post-2022), `ut` (for universal tabulator files).
Dominion does not have a schema validation currently.

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

### Fill in missing transfer data
Transfer data is useful to determine where votes went when a candidate was eliminated, or when a candidate was elected and had surplus votes (in STV).

If you have a file format that does not have transfer data, there are three options: you can leave it out entirely, you can assign transfers proportionally to each eliminated candidate, or you can assign only the transfers that are unambiguous.
We recommend the last option, which prepares transfer data for any round that does not involve batch elimination.
The second option results in fake data which cannot be relied upon for any results reporting or analyses.

## Multi-converters
Call `DominionMultiConverter.explode_to_files(fileObject)`, which will return a dictionary mapping election names to NamedTemporaryFiles.

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
In addition to data normalization for RCV Summary formats, we would like similar functionality for cast vote records.

## Running test suite
`pip3 install -r requirements-test.txt`, then run `python3 -m nose` in the root directory, and `./scripts/lint.sh` to run the linter.
