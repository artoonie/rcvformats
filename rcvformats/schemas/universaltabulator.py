"""
Loads the universal tabulator schema
"""

from rcvformats.schemas.base import GenericJsonSchema


class SchemaV0(GenericJsonSchema):
    """ Schema for the initial version of the Universal RCV Tabulator """

    @property
    def schema_filename(self):
        return 'universaltabulator.schema.json'

    def version(self):
        return "Unversioned:V0"
