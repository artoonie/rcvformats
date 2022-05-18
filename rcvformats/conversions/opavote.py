"""
Reads an ElectionBuddy CSV results file, writes to the standard format
"""

import json

from rcvformats.conversions.base import GenericGuessAtTransferConverter


class OpavoteConverter(GenericGuessAtTransferConverter):
    """
    Reads an opavote-formatted JSON file.
    """

    @classmethod
    def _get_eliminated_names(cls, rounds, candidate_names, round_i):
        """
        Opavote format places losses on the round after they happen, whereas
        the Universal Tabulator format places it on the previous round.
        This function looks at the next round for its data. A corellary is that
        there are no eliminations on the first round, which is what I believe to
        always be the case anyway.

        :param rounds: rounds data, direct from the Opavote format
        :param candidate_names: in-order names
        :param round_i: the current round (we'll look at round_i+1)
        :return: list of names that were eliminated
        """
        if round_i == len(rounds) - 1:
            ids = rounds[-1]['losers']
        else:
            ids = rounds[round_i + 1]['losers']
        return [candidate_names[i] for i in ids]

    @classmethod
    def _get_elected_names(cls, rounds, candidate_names, round_i):
        """
        :param candidate_names: in-order names
        :param rounds: rounds data, direct from the Opavote format
        :param round_i: the current round
        :return: list of names that were elected
        """
        ids = rounds[round_i]['winners']
        return [candidate_names[i] for i in ids]

    @classmethod
    def _votes_on_round(cls, candidate_i, rounds, round_i):
        """ Number of votes the corresponding candidate had on round_i """
        return rounds[round_i]['count'][candidate_i]

    def _convert_file_object_to_ut(self, file_object):
        data = json.load(file_object)

        threshold = sum(data['rounds'][-1]['count']) / (data['n_seats'] + 1)
        ut_config = {
            'contest': data['title'],
            'threshold': threshold
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
            for candidate_i, _ in enumerate(candidate_names):
                votes = self._votes_on_round(candidate_i, rounds, round_i)
                name = candidate_names[candidate_i]
                ut_round['tally'][name] = votes
            ut_rounds.append(ut_round)

        self._fill_in_tallyresults(rounds, candidate_names, ut_rounds)
        self._remove_eliminated_candidates_from_tally(rounds, candidate_names, ut_rounds)

        return {'config': ut_config, 'results': ut_rounds}

    @classmethod
    def _remove_eliminated_candidates_from_tally(cls, rounds, candidate_names, ut_rounds):
        for round_i in range(1, len(rounds)):
            already_eliminated = cls._get_eliminated_names(rounds, candidate_names, round_i - 1)
            for candidate_name in already_eliminated:
                del ut_rounds[round_i]['tally'][candidate_name]

    @classmethod
    def _fill_in_tallyresults(cls, rounds, candidate_names, ut_rounds):
        """ Fill out rounds['tallyResults'] based on rounds['tally'] """
        already_eliminated = set()
        already_elected = set()
        for round_i, _ in enumerate(rounds):
            # Get who was elected and eliminated
            eliminated_names = cls._get_eliminated_names(rounds, candidate_names, round_i)
            elected_names = cls._get_elected_names(rounds, candidate_names, round_i)

            # Opavote accumulates elected + eliminated candidates. Clean that up.
            eliminated_names = [n for n in eliminated_names if n not in already_eliminated]
            elected_names = [n for n in elected_names if n not in already_elected]

            # And save who was elected/eliminated for future rounds
            already_elected.update(elected_names)
            already_eliminated.update(eliminated_names)

            # Get how the votes change between this round and next
            vote_delta = cls.compute_vote_deltas_for_round(ut_rounds, round_i)

            # Use that to compute the tallyResults structure
            tally_results = cls.guess_at_tally_results(eliminated_names, elected_names, vote_delta)

            # Store it, completing the structure for this round
            ut_rounds[round_i]['tallyResults'] = tally_results
