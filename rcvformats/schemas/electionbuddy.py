"""
Loads the opavote schema
"""

from rcvformats.common.electionbuddyparser import ElectionBuddyData
from rcvformats.schemas.base import Schema


class SchemaV0(Schema):
    """
    ElectionBuddy's CSV format
    """

    def version(self):
        return 'unversioned:0'

    def _validate_file_object(self, file_object):
        try:
            ElectionBuddyData(file_object)
            return True
        except Exception as exception:  # pylint:disable=broad-except
            self._last_error = exception
            return False
