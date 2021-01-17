import abc

from rcvformats.schemas import universaltabulator


class CouldNotConvertException(Exception):
    """
    Raised when an unexpected error prevented conversion.
    This could be anything from an invalid input file, to unsupported data,
    to a bug in the software.
    """


class Conversion(abc.ABC):
    def __init__(self):
        """ Initializes common data """
        self.schema = universaltabulator.SchemaV0()
        self.has_been_parsed = False

    def to_universal_tabulator_format(self):
        """
        Returns a dictionary which you can serialize to the Universal RCV Tabulator format.
        :raises CouldNotConvertException: If the conversion could not complete
        """
        if not self.has_been_parsed:
            return CouldNotConvertException("You must call parse() first")

        try:
            ut_format = self._to_universal_tabulator_format()
            if not self.schema.validate_data(ut_format):
                raise CouldNotConvertException(self.schema.last_error())
        except Exception as e:
            raise CouldNotConvertException("Unexpected error")
        return ut_format

    def parse(self, filename):
        """
        Parses the file object and stores it internally for querying
        """
        self._parse(filename)
        self.has_been_parsed = True

    @abc.abstractmethod
    def _parse(self, filename):
        """
        Internal method called by parse(.):
        Parses the file object and stores it internally for querying
        :param filename: The filename to parse
        """

    @abc.abstractmethod
    def _to_universal_tabulator_format(self):
        """
        Internal method called by to_universal_tabulator_format():
        Returns a dictionary representation of the Universal RCV Tabulator format,
        which will be sanity-checked for correctness by to_universal_tabulator_format
        """
