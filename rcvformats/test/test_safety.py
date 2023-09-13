"""
Safety tests: enforce security measures here
"""
from openpyxl import DEFUSEDXML


def test_electionbuddy_conversions_succeed():
    """ Ensures defusedXml is installed to prevent malicious XML attacks """
    assert DEFUSEDXML
