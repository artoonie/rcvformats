"""
Reads an ElectionBuddy CSV results file, writes to the standard format
"""

import json

from rcvformats.conversions.base import GenericGuessAtTransferConverter


class OpavoteConverter(GenericGuessAtTransferConverter):
    """
    Reads an opavote-formatted JSON file.
    """

    def _get_eliminated_names(self, candidate_names, rounds, round_i):
        """
        Opavote format places losses on the round after they happen, whereas
        the Universal Tabulator format places it on the previous round.
        This function looks at the next round for its data. A corellary is that
        there are no eliminations on the first round, which is what I believe to
        always be the case anyway.

        :param candidate_names: in-order names
        :param rounds: rounds data, direct from the Opavote format
        :param round_i: the current round (we'll look at round_i+1)
        :return: list of names that were eliminated
        """
        if round_i == len(rounds) - 1:
            return []
        ids = rounds[round_i + 1]['losers']
        return [candidate_names[i] for i in ids]

    def _get_elected_names(self, candidate_names, rounds, round_i):
        """
        :param candidate_names: in-order names
        :param rounds: rounds data, direct from the Opavote format
        :param round_i: the current round
        :return: list of names that were elected
        """
        ids = rounds[round_i]['winners']
        return [candidate_names[i] for i in ids]

    def _votes_on_round(self, candidate_i, rounds, round_i):
        """ Number of votes the corresponding candidate had on round_i """
        return rounds[round_i]['count'][candidate_i]

    def _parse(self, filename):
        with open(filename, 'r') as file_object:
            data = json.load(file_object)

        threshold = sum(data['rounds'][-1]['count']) / (data['n_seats'] + 1)
        ut_config = {
            'contest': data['title'],
            'threshold': threshold,
            'date': self.guess_at_date(filename)
        }

        # Fill out rounds['tally']
        rounds = data['rounds']
        candidate_names = data['candidates']
        ut_rounds = []
        for round_i in range(len(rounds)):
            ut_round = {
                'round': round_i + 1,
                'tally': {}
            }
            for candidate_i in range(len(candidate_names)):
                votes = self._votes_on_round(candidate_i, rounds, round_i)
                name = candidate_names[candidate_i]
                ut_round['tally'][name] = votes
            ut_rounds.append(ut_round)

        # Fill out rounds['tallyResults'] based on rounds['tally']
        already_eliminated = set()
        for round_i, round_data in enumerate(rounds):
            # Get who was elected and eliminated
            eliminated_names = self._get_eliminated_names(candidate_names, rounds, round_i)
            elected_names = self._get_elected_names(candidate_names, rounds, round_i)
            # Opavote accumulates eliminated candidates. Clean that up.
            eliminated_names = [n for n in eliminated_names if n not in already_eliminated]
            already_eliminated.update(eliminated_names)
            # Get how the votes change between this round and next
            vote_delta = self.compute_vote_deltas_for_round(ut_rounds, round_i)
            # Use that to compute the tallyResults structure
            tallyResults = self.guess_at_tally_results(eliminated_names, elected_names, vote_delta)
            # Store it, completing the structure for this round
            ut_rounds[round_i]['tallyResults'] = tallyResults

        self.ut_formatted_data = {'config': ut_config, 'results': ut_rounds}

    def _to_universal_tabulator_format(self):
        return self.ut_formatted_data
