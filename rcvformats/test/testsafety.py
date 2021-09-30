"""
Safety tests: enforce security measures here
"""
import nose
from openpyxl import DEFUSEDXML


def test_electionbuddy_conversions_succeed():
    """ Ensures defusedXml is installed to prevent malicious XML attacks """
    nose.tools.assert_true(DEFUSEDXML)
