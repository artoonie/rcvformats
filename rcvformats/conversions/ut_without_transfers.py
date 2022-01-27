"""
Add transfers to an otherwise-valid Universal Tabulator format
"""

import json

from rcvformats.conversions.base import GenericGuessAtTransferConverter


class UTWithoutTransfersConverter(GenericGuessAtTransferConverter):
    """
    Reads an UT-formatted JSON file that is missing "transfers"
    """

    def __init__(self, allow_guessing=True):
        """
        @param allow_guessing During batch elimination, should we guess at
                              where the votes went (distributing them proportionally)
                              or leave this blank?
        """
        self.allow_guessing = allow_guessing
        super().__init__()

    def _convert_json_to_ut(self, json_data):
        return self.fill_in_tally_data(json_data)

    def _convert_file_object_to_ut(self, file_object):
        data = json.load(file_object)
        return self._convert_json_to_ut(data)

    def fill_in_tally_data(self, data):
        """ Given data in the UT format, fill in the tallyResults """
        self._convert_tally_string_to_decimal(data['results'])
        self._fill_in_tallyresults(data['results'])
        return data

    @classmethod
    def _get_eliminated_names(cls, rounds, round_i):
        """ Reads each tallyResult, returns any eliminated name """
        results = rounds[round_i]['tallyResults']
        return [d['eliminated'] for d in results if 'eliminated' in d]

    @classmethod
    def _get_elected_names(cls, rounds, round_i):
        """ Reads each tallyResult, returns any elected name """
        results = rounds[round_i]['tallyResults']
        return [d['elected'] for d in results if 'elected' in d]

    @classmethod
    def _convert_tally_string_to_decimal(cls, rounds):
        for round_data in rounds:
            for person in round_data['tally']:
                round_data['tally'][person] = float(round_data['tally'][person])

    def _fill_in_tallyresults(self, rounds):
        """ Fill out rounds['tallyResults'] based on rounds['tally'] """
        for round_i, _ in enumerate(rounds):
            # Get who was elected and eliminated
            eliminated_names = self._get_eliminated_names(rounds, round_i)
            elected_names = self._get_elected_names(rounds, round_i)

            # Get how the votes change between this round and next
            vote_delta = self.compute_vote_deltas_for_round(rounds, round_i)

            # Use that to compute the tallyResults structure
            tally_results = self.guess_at_tally_results(
                eliminated_names, elected_names, vote_delta, self.allow_guessing)

            # Store it, completing the structure for this round
            rounds[round_i]['tallyResults'] = tally_results
