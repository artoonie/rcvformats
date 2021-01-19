"""
Loads the opavote schema
"""

from rcvformats.schemas.base import GenericJsonSchema


#  pylint:disable=invalid-name
class SchemaV1_0(GenericJsonSchema):
    """ Schema for the initial version of the Universal RCV Tabulator """

    @property
    def schema_filename(self):
        return 'opavote.schema.json'

    def version(self):
        return "1.0"
