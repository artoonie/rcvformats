#!/usr/bin/env python

"""
A command-line interface to some of the python functionality
"""

import argparse
import json
import sys

from enum import Enum

from rcvformats.schemas import electionbuddy
from rcvformats.schemas import universaltabulator
from rcvformats.schemas import opavote
from rcvformats.conversions.automatic import AutomaticConverter
from rcvformats.conversions.ut_without_transfers import UTWithoutTransfersConverter


class FormatEnum(Enum):
    """ Enum for validator, and perhaps eventually converter. """
    UT = 'ut'
    EB = 'eb'
    OV10 = 'ov10'
    OV11 = 'ov11'

    def __str__(self):
        return str(self.value)


def convert(input_filename, output_filename):
    """ Automatic converter from input_filename to output_filename """
    standardized_format = AutomaticConverter().convert_to_ut(input_filename)
    with open(output_filename, 'w', encoding='utf-8') as file_obj:
        json.dump(standardized_format, file_obj)


def validate(input_filename, schema):
    """ validates input_filename with schema """
    if schema == FormatEnum.UT:
        schema = universaltabulator.SchemaV0()
    elif schema == FormatEnum.EB:
        schema = electionbuddy.SchemaV0()
    elif schema == FormatEnum.OV10:
        schema = opavote.SchemaV1_0()
    elif schema == FormatEnum.OV11:
        schema = opavote.SchemaV1_1()

    is_valid = schema.validate(input_filename)
    if is_valid:
        print("Schema is valid.")
    else:
        print("Schema is not valid. Errors: ", schema.last_error())


def add_transfers(input_filename, output_filename, allow_guessing):
    """ Adds tally transfers if they don't exist. Overwrites them if they do. """
    # Adding transfers, internally, is just another conversion
    converter = UTWithoutTransfersConverter(allow_guessing=allow_guessing)
    with_transfers = converter.convert_to_ut(input_filename)
    with open(output_filename, 'w', encoding='utf-8') as file_obj:
        json.dump(with_transfers, file_obj)


def _add_input_arg(parser):
    parser.add_argument(
        '-i',
        '--input',
        dest='input_filename',
        help='File to convert',
        required=True)


def _add_output_arg(parser):
    parser.add_argument(
        '-o',
        '--output',
        dest='output_filename',
        help='Where to place the JSON file on success',
        required=True)


def main():
    """ Main function: cli entrypoint, using argparse """
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        dest='subparser',
        help='Tooling for RCV Formats. See more at https://rcvformats.readthedocs.io/en/latest/')

    conv_parser = subparsers.add_parser(
        'convert', help='Converts from whatever format you have to the Universal Tabulator format.')
    _add_input_arg(conv_parser)
    _add_output_arg(conv_parser)

    validate_parser = subparsers.add_parser(
        'validate', help='Validates the file with one of the three accepted formats')
    _add_input_arg(validate_parser)
    validate_parser.add_argument(
        '-s',
        '--schema',
        dest='schema',
        type=FormatEnum,
        choices=list(FormatEnum),
        help='Schema to validate against: ut (Universal Tabulator/RCTab), '
             'eb (ElectionBuddy), or ov (OpaVote)',
        required=True)

    xfer_parser = subparsers.add_parser(
        'transfer', help='Adds "transfers" to the tallyResults of an otherwise-valid UI format')
    _add_input_arg(xfer_parser)
    _add_output_arg(xfer_parser)
    xfer_parser.add_argument(
        '-g',
        '--allow-guessing',
        dest='allow_guessing',
        action='store_true',
        help='During batch elimination, may we guess at the vote transfers? '
             'If not, will leave transfers blank for all batch elimination rounds.',
        required=False)

    args = parser.parse_args()
    if args.subparser is None:
        print(parser.print_help())
        sys.exit(-1)

    if args.subparser == 'convert':
        convert(args.input_filename, args.output_filename)
    if args.subparser == 'validate':
        validate(args.input_filename, args.schema)
    if args.subparser == 'transfer':
        add_transfers(args.input_filename, args.output_filename, args.allow_guessing)
