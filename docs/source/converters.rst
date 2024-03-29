##################
Converters
##################

.. toctree::
   :maxdepth: 1

Interface
-----------------------

All converters conform to this interface.

.. automodule:: conversions.base
   :members: Converter
   :show-inheritance:

Exceptions
-----------------------

Some of the possible exceptions that may be thrown during conversion

.. automodule:: conversions.base
   :members: CouldNotConvertException
   :private-members:
   :show-inheritance:
   :noindex:

Automatic Converter
-----------------------

Allows you to provide any file and it will try to figure out its type and convert it.

.. automodule:: conversions.automatic
   :members:
   :private-members:
   :show-inheritance:

Internal developer documentation
--------------------------------
The remainder of this documentation is about the internal representation of classes.
It is intended for developers of RCV Formats, rather than its users.


Transferless format helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Helper base class for any file format which does not explicitly spell out how
votes are transferred between candidates.

.. automodule:: conversions.base
   :members: GenericGuessAtTransferConverter
   :private-members:
   :show-inheritance:
   :noindex:

Opavote to Universal Tabulator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: conversions.opavote
   :members:
   :private-members:
   :show-inheritance:

ElectionBuddy to Universal Tabulator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: conversions.electionbuddy
   :members:
   :private-members:
   :show-inheritance:

Dominion to Universal Tabulator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: conversions.dominion_txt
   :members:
   :private-members:
   :show-inheritance:

.. automodule:: conversions.dominion_xlsx
   :members:
   :private-members:
   :show-inheritance:

.. automodule:: conversions.dominion_multi_converter
   :members:
   :private-members:
   :show-inheritance:
