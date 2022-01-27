"""
Interface and exceptions for all converters
"""

import abc

from rcvformats.common import utils
from rcvformats.schemas import universaltabulator


class CouldNotConvertException(Exception):
    """
    Raised when an unexpected error prevented conversion.
    This could be anything from an invalid input file, to unsupported data,
    to a bug in the software.
    """


class CouldNotOpenFileException(Exception):
    """
    Raised if the file could not be opened
    """


class Converter(abc.ABC):
    """ Interface for converters """

    def __init__(self):
        """ Initializes common data """
        self.ut_schema = universaltabulator.SchemaV0()

    def convert_to_ut_and_validate(self, filename_or_fileobj):
        """
        Calls :func:`~convert_to_ut`, then validates it with the Universal Tabulator schema.

        :param filename: A File object or filename
        :return: Guaranteed-valid Universal Tabulator data
        :raises CouldNotConvertException: If the conversion could not complete
        """
        ut_format = self.convert_to_ut(filename_or_fileobj)
        if not self.ut_schema.validate_schema_and_logic(ut_format):
            raise CouldNotConvertException(self.ut_schema.last_error())

        return ut_format

    def convert_to_ut(self, data):
        """
        Parses the file and returns the parsed data

        :param data: A File object, filename, or json data. Not all converters support JSON.
        :return: The Universal Tabulator representation of this data.\
                 Call :func:`~convert_to_ut_and_validate` to guarantee that \
                 it matches the Universal Tabulator schema.
        :raises CouldNotConvertException: If the conversion could not complete
        :raises CouldNotOpenFileException: If the file couldn't be opened
        """
        try:
            if isinstance(data, dict):
                return self._convert_json_to_ut(data)
            if utils.is_file_obj(data):
                return self._convert_file_object_to_ut(data)
            if utils.is_filename(data):
                with open(data, 'rb') as file_object:
                    return self._convert_file_object_to_ut(file_object)
        except CouldNotConvertException as known_error:
            raise known_error
        except Exception as unknown_error:
            raise CouldNotConvertException(str(unknown_error)) from unknown_error

        raise CouldNotOpenFileException(f"Could not open {data}")

    def _convert_json_to_ut(self, json_data):
        """
        Optional. Only some converters support JSON.
        """
        raise NotImplementedError("This converter does not support JSON data.")

    @abc.abstractmethod
    def _convert_file_object_to_ut(self, file_object):
        """
        Just like func:`~convert_to_ut`, but only accepting a file object
        """


class GenericGuessAtTransferConverter(Converter):
    """
    If there are multiple candidates transferring their votes, we cannot know
    which candidates contributed to which transfers.
    Our best-effort guess is that they distributed their votes equally to all candidates.

    This base class lets you fill out partial data, leaving out tallyResults,
    and it will guess at the tallyResults for you.

    Note that it always knows the correct tally results if only one candidate is
    eliminated or elected in each round - the guessing only happens when multiple
    candidates are transferring their votes.
    """

    @classmethod
    def _weights_for_each_transfer(cls, eliminated_names, elected_names, vote_delta):
        """
        :param eliminated_names: the names of each eliminated candidate
        :param elected_names: the names of each elected candidate
        :param vote_delta: a dict mapping candidate name to vote difference
                           between this round and the next round
        :return: a dict mapping a transferring candidate's name to the weight they contributed
                to the overall transfer. In most cases, there will only be one candidate in
                transferring_candidates and the weight will be a simple 1.0.
        """
        # Names of both eliminated and elected candidates (elected may or may not have surpluses)
        transferring_candidates = eliminated_names + elected_names

        # How many votes are being transferred?
        votes_subtracted = -sum(d for d in vote_delta.values() if d < 0)

        weights = {
            name: -vote_delta[name] / votes_subtracted if votes_subtracted != 0 else 1
            for name in transferring_candidates
        }

        # Sanity check 1: weights must add up to 1
        if votes_subtracted != 0:
            if abs(sum(weights.values()) - 1.0) > 1e-8:
                votes_gained = sum(vote_delta.values())
                message = "Weights do not line up. This data is invalid. "\
                          f"In the round where {eliminated_names} were eliminated and "\
                          f"{elected_names} were elected, there were {votes_subtracted} "\
                          f"votes lost from the outgoing candidates, but {votes_gained} "\
                          "votes gained from continuing candidates. The number of votes must "\
                          "stay the same or decrease between rounds."
                raise ValueError(message)

        # Sanity check 2: can't gain more votes than you lost.
        # Exhausted ballots account for the inequality: lost ballots that were not gained anywhere
        votes_added = sum(d for d in vote_delta.values() if d > 0)
        assert votes_subtracted >= votes_added

        return weights

    @classmethod
    def _compute_vote_deltas_from_tally(cls, tally_this_round, tally_next_round):
        """
        Returns the vote deltas between this round and next round. The two tally arguments
        must match the tally format in the Universal Tabulator format.

        :param tally_this_round: A dict mapping candidate names to number of votes this round
        :param tally_next_round: A dict mapping candidate names to number of votes next round,\
                                 ensuring that any eliminated candidates are NOT present next\
                                 round, NOT that they just have zero votes.
        :return: A dict mapping candidate names in this round to how their votes changed
                 between this round and the next. Includes positive numbers (gained votes) and
                 negative numbers (lost votes via elimination or surplus transfer)
        """
        # Check who is no longer around next round
        eliminated_names = [name for name in tally_this_round if name not in tally_next_round]

        # Same as tally_next_round but includes 0 for eliminated candidates
        numvotes_next_round = {
            name: tally_next_round[name] if name not in eliminated_names else 0
            for name in tally_this_round
        }

        # Compute the difference for each candidate in this round
        return {
            to_name: numvotes_next_round[to_name] - tally_this_round[to_name]
            for to_name in tally_this_round
        }

    @classmethod
    def compute_vote_deltas_for_round(cls, ut_rounds_tally_only, round_i):
        """
        Gathers some data and passes it on to :func:`~_compute_vote_deltas_from_tally`

        :param ut_rounds_tally_only: Incomplete Universal Tabulator 'results' structure, \
                                     containing only 'tally' but not 'tallyResults'. \
                                     The tallies must be numbers, not strings.
        :param round_i: Computes delta between this round and the next
        :return: Value from :func:`~_compute_vote_deltas_from_tally`
        """
        if round_i == len(ut_rounds_tally_only) - 1:
            # Last round - no deltas
            return {}
        tally_this_round = ut_rounds_tally_only[round_i]['tally']
        tally_next_round = ut_rounds_tally_only[round_i + 1]['tally']
        return cls._compute_vote_deltas_from_tally(tally_this_round, tally_next_round)

    @classmethod
    def guess_at_tally_results(
            cls,
            eliminated_names,
            elected_names,
            vote_delta,
            allow_guessing=True):
        """
        Computes the tallyResult, the difference between this round and the next
        See the description of @_compute_tally_results to understand why, in the case of
        multiple winners, the best we can do is guess at the transfers here.

        :param eliminated_names: the names of each eliminated candidate
        :param elected_names: the names of each elected candidate
        :param vote_delta: a dict mapping candidate name to vote difference \
                           between this round and the next round.
        :param allow_guessing: Allow guessing of transfer data during batch elimination
        :return: The contents of the tallyResults dict
        """
        weights = cls._weights_for_each_transfer(eliminated_names, elected_names, vote_delta)

        # Loop over each eliminated or elected candidate and generate the transfers to
        # continuing candidates
        tally_results = []
        transfer_methods = {
            'eliminated': eliminated_names,
            'elected': elected_names
        }
        names_to_transfer_to = [name for name in vote_delta.keys() if
                                name not in eliminated_names and
                                name not in elected_names]
        for method, names in transfer_methods.items():
            for from_name in names:
                tally_result = {}
                tally_result[method] = from_name
                is_batch_elimination_round = len(names) > 1
                if not is_batch_elimination_round or allow_guessing:
                    transfers = {
                        to_name: vote_delta[to_name] * weights[from_name]
                        for to_name in names_to_transfer_to
                        if vote_delta[to_name] != 0
                    }
                else:
                    transfers = {}
                if transfers or method == 'eliminated':
                    # only add transfers on winners if they have actually been transferred
                    tally_result['transfers'] = transfers

                tally_results.append(tally_result)
        return tally_results
