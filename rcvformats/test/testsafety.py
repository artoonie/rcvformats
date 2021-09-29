import nose
import defusedxml
from openpyxl import DEFUSEDXML

def test_electionbuddy_conversions_succeed():
    """ Ensures defusedXml is installed to prevent malicious XML attacks """
    nose.tools.assert_true(DEFUSEDXML)
