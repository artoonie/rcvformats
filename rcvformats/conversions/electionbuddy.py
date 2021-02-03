"""
Reads an ElectionBuddy CSV results file, writes to the standard format
"""

from rcvformats.common.electionbuddyparser import ElectionBuddyData
from rcvformats.conversions.base import GenericGuessAtTransferConverter


class ElectionBuddyConverter(GenericGuessAtTransferConverter):
    """
    Reads an electionbuddy-formatted CSV file. Note that this
    use a generic text file reader, not a CSV reader, because
    it's not really a CSV file - it has parts of it that are,
    but it also has miscellaneous title lines.
    """

    def _convert_file_object_to_ut(self, file_object):
        raw_data = ElectionBuddyData(file_object)

        # Create configuration, assuming date of election is the file creation date
        config = {
            'contest': raw_data.title.strip(),
            'threshold': str(self._get_threshold(raw_data))
        }

        # Loop over each round, first filling in just the tally
        ut_rounds = self._get_round_data_without_tallyresults(raw_data.rounds)

        # Then, compute the tally results
        self._fill_in_tallyresults_from_tally(raw_data.rounds, ut_rounds)

        return {'config': config, 'results': ut_rounds}

    @classmethod
    def _get_round_data_without_tallyresults(cls, rounds):
        """ Generates the ut_rounds data without tallyResults """
        ut_rounds = []
        for round_i, round_data in enumerate(rounds):
            ut_round = {
                'round': round_i + 1,
                'tally': {}
            }
            candidates = round_data['candidates']
            for candidate, votes in candidates.items():
                ut_round['tally'][candidate] = votes
            ut_rounds.append(ut_round)
        return ut_rounds

    @classmethod
    def _fill_in_tallyresults_from_tally(cls, rounds, ut_rounds):
        """ Fills in tallyResults in ut_rounds """
        already_elected_set = set()
        for round_i in range(len(rounds)):
            # Get who was elected and eliminated
            elected_names = cls._get_elected_names(rounds, round_i, already_elected_set)
            eliminated_names = cls._get_eliminated_names(rounds, round_i)
            # Get how the votes change between this round and next
            vote_delta = cls.compute_vote_deltas_for_round(ut_rounds, round_i)
            # Use that to compute the tallyResults structure
            tally_results = cls.guess_at_tally_results(eliminated_names, elected_names, vote_delta)
            # Store it, completing the structure for this round
            ut_rounds[round_i]['tallyResults'] = tally_results

    @classmethod
    def _threshold_for_round(cls, rounds, round_i):
        """
        If the threshold is not provided in each round, assume it is half of the number
        of voters present in the last round. This means that if the thresold is not
        provided, we assume it is a single-winner election (unless there is an exact 50/50 tie)
        TODO: This should probably be handled by a migration function, since
        ElectionBuddy no longer outputs data without thresholds.
        """
        if rounds[round_i]['threshold']:
            return rounds[round_i]['threshold']

        last_round = rounds[-1]
        num_voters_in_last_round = sum([v for k, v in last_round['candidates'].items()])
        return num_voters_in_last_round / 2.0

    @classmethod
    def _get_eliminated_names(cls, rounds, round_i):
        if round_i == len(rounds) - 1:
            return []

        thisround_candidates = set(rounds[round_i]['candidates'])
        nextround_candidates = set(rounds[round_i + 1]['candidates'])

        # Check who is no longer around next round
        return list(thisround_candidates - nextround_candidates)

    @classmethod
    def _get_elected_names(cls, rounds, round_i, already_elected_set):
        """ :return: a list of names of candidates elected on this round """
        candidates = rounds[round_i]['candidates']
        threshold = cls._threshold_for_round(rounds, round_i)
        elected_names = [name for name in candidates if candidates[name]
                         > threshold and name not in already_elected_set]
        already_elected_set.update(elected_names)
        return elected_names

    @classmethod
    def _get_threshold(cls, csv_data):
        """
        Returns the threshold for the overall election, which doesn't make a lot of sense
        for dynamic-threshold multiwinner elections, but we mark it as just the last
        threshold in the file if the file contains thresholds.
        """
        last_round = csv_data.rounds[-1]
        if last_round['threshold']:
            return last_round['threshold']

        num_voters_in_last_round = sum([v for k, v in last_round['candidates'].items()])
        return num_voters_in_last_round / 2.0
