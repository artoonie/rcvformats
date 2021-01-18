import abc
import os
import time


from rcvformats.schemas import universaltabulator


class CouldNotConvertException(Exception):
    """
    Raised when an unexpected error prevented conversion.
    This could be anything from an invalid input file, to unsupported data,
    to a bug in the software.
    """


class Converter(abc.ABC):
    def __init__(self):
        """ Initializes common data """
        self.schema = universaltabulator.SchemaV0()
        self.has_been_parsed = False

    def guess_at_date(self, filename):
        """
        If the file format has no date, guess it by the file mtime
        :param filename: The filename to inspect
        :return: A string representing the Y-m-d
        """
        date_file_created = time.gmtime(os.path.getmtime(filename))
        return time.strftime('%Y-%m-%d', date_file_created)

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

    def _weights_for_each_transfer(self, eliminated_names, elected_names, vote_delta):
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
            assert abs(sum(weights.values()) - 1.0) < 1e-8

        # Sanity check 2: can't gain more votes than you lost.
        # Exhausted ballots account for the inequality: lost ballots that were not gained anywhere
        votes_added = sum(d for d in vote_delta.values() if d > 0)
        assert votes_subtracted >= votes_added

        return weights

    def _compute_vote_deltas_from_tally(self, tally_this_round, tally_next_round):
        """
        Returns the vote deltas between this round and next round. The two tally arguments
        must match the tally format in the Universal Tabulator format.
        :param tally_this_round: A dict mapping candidate names to number of votes this round
        :param tally_next_round: A dict mapping candidate names to number of votes next round,
                                 ensuring that any eliminated candidates are NOT present next
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

    def compute_vote_deltas_for_round(self, ut_rounds_tally_only, round_i):
        """
        Wrapper around
        :param ut_rounds_tally_only: Incomplete Universal Tabulator 'results' structure,
            containing only 'tally' but not 'tallyResults'. The tallies must be numbers,
            not strings.
        :return: Value from _compute_vote_deltas_from_tally
        """
        if round_i == len(ut_rounds_tally_only) - 1:
            # Last round - no deltas
            return {}
        tally_this_round = ut_rounds_tally_only[round_i]['tally']
        tally_next_round = ut_rounds_tally_only[round_i + 1]['tally']
        return self._compute_vote_deltas_from_tally(tally_this_round, tally_next_round)

    def guess_at_tally_results(self, eliminated_names, elected_names, vote_delta):
        """
        Computes the tallyResult, the difference between this round and the next
        :param eliminated_names: the names of each eliminated candidate
        :param elected_names: the names of each elected candidate
        :param vote_delta: a dict mapping candidate name to vote difference
                           between this round and the next round.
        :return: The contents of the tallyResults dict

        See the description of @_compute_tally_results to understand why, in the case of
        multiple winners, the best we can do is guess at the tranfsers here.
        """
        weights = self._weights_for_each_transfer(eliminated_names, elected_names, vote_delta)

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
                tally_result['transfers'] = {
                    to_name: vote_delta[to_name] * weights[from_name]
                    for to_name in names_to_transfer_to
                    if vote_delta[to_name] != 0
                }
                tally_results.append(tally_result)
        return tally_results
