##################
Schemas
##################

.. toctree::
   :maxdepth: 1

Interface
-----------------------

All schemas conform to this interface.

.. automodule:: schemas.base
   :members: Schema
   :show-inheritance:

Internal developer documentation
--------------------------------
The remainder of this documentation is about the internal representation of classes.
It is intended for developers of RCV Formats, rather than its users.

JSONSchema helper
^^^^^^^^^^^^^^^^^^^^^^^
A helper interface for all jsonschema-backed schemas

.. automodule:: schemas.base
   :members: GenericJsonSchema
   :show-inheritance:
   :noindex:


Universal Tabulator
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: schemas.universaltabulator
   :members:
   :private-members:
   :show-inheritance:

Opavote
^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: schemas.opavote
   :members:
   :private-members:
   :show-inheritance:
