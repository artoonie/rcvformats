"""
Loads the universal tabulator schema
"""

from rcvformats.schemas.base import GenericJsonSchema, DataError


class SchemaV0(GenericJsonSchema):
    """ Schema for the initial version of the Universal RCV Tabulator """

    @property
    def schema_filename(self):
        return 'universaltabulator.schema.json'

    def version(self):
        return "Unversioned:V0"

    def ensure_data_is_logical(self, data):
        """
        Various checks to ensure the data is sane - though it cannot catch everything,
        we have tried to place the most common errors here
        """
        self.check_last_round_eliminations(data)
        self.check_candidate_leaves_after_elimination(data)
        self.check_unique_candidate_names(data)
        self.check_no_empty_candidate_names(data)
        self.check_votes_never_decrease_except_surplus(data)

    @classmethod
    def check_unique_candidate_names(cls, data):
        """
        All candidate names must be unique
        """
        first_round_tally = data['results'][0]['tally']
        names = first_round_tally.keys()
        if len(set(names)) != len(names):
            raise DataError("All candidate names must be unique.")

    @classmethod
    def check_no_empty_candidate_names(cls, data):
        """
        All candidate names must be unique
        """
        first_round_tally = data['results'][0]['tally']
        names = first_round_tally.keys()
        if any(n == "" for n in names):
            raise DataError("All candidates must have non-empty names.")

    @classmethod
    def check_last_round_eliminations(cls, data):
        """
        No eliminations allowed on the last round
        """
        last_round_tally_results = data['results'][-1]['tallyResults']
        for tally_result in last_round_tally_results:
            if 'eliminated' in tally_result:
                raise DataError(
                    "There cannot be an elimination on the last round. "
                    "All eliminations require one additional round to signify where the "
                    "votes have been transferred to.")

    @classmethod
    def check_votes_never_decrease_except_surplus(cls, data):
        """
        Check that the vote counts never decrease, except in the case of surplus transfers.
        """
        first_round_tally = data['results'][0]['tally']
        prev_round_counts = first_round_tally
        prev_round_winners = set()
        for round_num, result in enumerate(data['results']):
            tally = result['tally']
            for name in tally:
                this_round_count = float(tally[name])
                if this_round_count >= float(prev_round_counts[name]):
                    continue

                if this_round_count == 0:
                    raise DataError("Vote count should not decrease to zero. Candidate "
                                    f"{name} should be eliminated on Round {round_num}.")
                if name not in prev_round_winners:
                    raise DataError("Vote counts should never decrease except in the case of "
                                    f"a surplus transfer. Candidate {name}'s votes decreased "
                                    f"from {prev_round_counts[name]} to {this_round_count} "
                                    f"on Round {round_num+1}, but they were not elected on "
                                    f"Round {round_num}.")
            prev_round_winners = {tr['elected'] for tr in result['tallyResults'] if 'elected' in tr}
            prev_round_counts = tally

    @classmethod
    def check_candidate_leaves_after_elimination(cls, data):
        """
        After a candidate is eliminated, ensure they are not listed later as having
        zero votes. They should be removed from the list.
        """
        eliminated_so_far = set()
        for round_num, result in enumerate(data['results']):
            tally = result['tally']
            for name in tally:
                if name in eliminated_so_far:
                    raise DataError(
                        f"Found {name} in Round {round_num+1}, though they were "
                        "already eliminated. After a candidate is eliminated, they should "
                        "be removed from all future vote tallies.")

            eliminated_so_far.update(
                {tr['eliminated'] for tr in result['tallyResults'] if 'eliminated' in tr})
