"""
Loads the opavote schema
"""

from rcvformats.schemas.base import GenericJsonSchema


#  pylint:disable=invalid-name
class SchemaV1_0(GenericJsonSchema):
    """ Schema for the initial Opavote schema """

    @property
    def schema_filename(self):
        return 'opavote.schema.json'

    def version(self):
        return "1.0"

#  pylint:disable=invalid-name


class SchemaV1_1(GenericJsonSchema):
    """ Schema for the version created on 2022-05-18 """

    @property
    def schema_filename(self):
        return 'opavote_v1_1.schema.json'

    def version(self):
        return "1.1"
