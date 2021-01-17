"""
Reads an ElectionBuddy CSV results file, writes to the standard format
"""

import os
import time

from rcvformats.conversions.base import Conversion

class RawFileData:
    """
    Structure to hold the raw data read from the file.
    Parses the data directly into a simple format to make it easier for CSVReader to work with.
    """
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.title = self.read_line_as_str()
        self.read_line_as_str()  # line break

        self.position = self.read_line_as_str()
        self.read_line_as_str()  # stars
        self.read_line_as_str()  # line break

        self.read_each_round()

    def read_line_as_str(self):
        """ Read line, and if it's bytes, decode to utf-8 """
        line = self.file_obj.readline()
        if isinstance(line, bytes):
            return line.decode("utf-8")
        return line

    def peek_line(self):
        """ Peeks at the next line without advancing """
        pos = self.file_obj.tell()
        line = self.read_line_as_str()
        self.file_obj.seek(pos)
        return line

    def read_each_round(self):
        """ Start iterating over the CSV for each round """
        self.rounds = []
        while self.file_obj:
            roundText = self.read_line_as_str()
            if not roundText.startswith("Round"):
                assert len(self.rounds) > 0
                break

            self.rounds.append(self.read_round())

    def read_round(self):
        """ Reads the CSV data for the next round """
        headers = self.read_line_as_str()
        assert headers.strip() == "Candidate,Votes,Percentage"

        candidates = {}
        threshold = None
        while True:
            line = self.read_line_as_str()
            if line.strip() == "":
                break
            candidate, votes, _ = line.split(',')
            candidates[candidate] = float(votes)

        # Eat summary lines (votes tallied, abstentions, newline)
        line = self.read_line_as_str()
        assert line.startswith('Votes tallied')

        # There are two optional lines: abstentions and threshold.
        # Check for each.
        for _ in range(2):
            line = self.peek_line()
            if line.startswith('Abstentions: '):
                # Abstentions line is optional
                self.read_line_as_str()
            elif line.startswith('Threshold: '):
                # Threshold line is optional
                line = self.read_line_as_str()
                thresholdStr = line[len('Threshold: '):]
                threshold = float(thresholdStr)
            else:
                assert line.strip() == ''
                break

        # Check for newline
        line = self.read_line_as_str()
        assert line.strip() == ''

        return {'candidates': candidates,
                'threshold': threshold}


class CSVReader(Conversion):
    """
    Reads an electionbuddy-formatted CSV file. Note that this
    use a generic text file reader, not a CSV reader, because
    it's not really a CSV file - it has parts of it that are,
    but it also has miscellaneous title lines.
    """

    def _parse(self, filename):
        with open(filename, 'r') as file_object:
            raw_data = RawFileData(file_object)

        # Create configuration, assuming date of election is the file creation date
        date_file_created = time.gmtime(os.path.getmtime(filename))
        ut_config = {
            'contest': raw_data.title.strip(),
            'threshold': str(self._get_threshold(raw_data)),
            'date': time.strftime('%Y-%m-%d', date_file_created)
            
        }

        # Loop over each round
        ut_rounds = []
        self.already_elected = []
        for round_i, round_data in enumerate(raw_data.rounds):
            ut_round = {
                'round': round_i + 1,
                'tally': {},
                'tallyResults': []
            }
            candidates = round_data['candidates']
            for candidate, votes in candidates.items():
                ut_round['tally'][candidate] = str(votes)
            ut_round['tallyResults'] = self._compute_tally_results(raw_data.rounds, round_i)
            ut_rounds.append(ut_round)

        self.ut_config = ut_config
        self.ut_rounds = ut_rounds

    def _to_universal_tabulator_format(self):
        return {'config': self.ut_config, 'results': self.ut_rounds}

    def _threshold_for_round(self, rounds, round_i):
        """
        If the threshold is not provided in each round, assume it is half of the number
        of voters present in the last round. This means that if the thresold is not
        provided, we assume it is a single-winner election (unless there is an exact 50/50 tie)
        TODO: This should probably be handled by a migration function, since
        ElectionBuddy no longer outputs data without thresholds.
        """
        if rounds[round_i]['threshold']:
            return rounds[round_i]['threshold']

        lastRound = rounds[-1]
        numVotersInLastRound = sum([v for k, v in lastRound['candidates'].items()])
        return numVotersInLastRound / 2.0

    def _what_happens_next_round(self, rounds, round_i):
        """
        Describes what happens next round.
        :param rounds: the rounds from CSVReader.rounds
        :param round_i: the current round
        :return: A dict containing:
            nextround_candidates: the candidates continuing to the next round
            eliminated_names: the candidates eliminated this round
            vote_delta: how much each candidate's votes change
        """
        candidates = rounds[round_i]['candidates']

        # Eliminations & transfers
        # On any round but the last, there can be eliminated candidates and transfers.
        # Don't include negative surplus-vote transfers: those are implicit.
        if round_i != len(rounds) - 1:
            # The candidate-to-votes dict of the next round
            nextround_candidates = rounds[round_i+1]['candidates']

            # Check who is no longer around next round
            eliminated_names = [name for name in candidates if name not in nextround_candidates]

            # Same as nextround_candidates but includes 0 for eliminated candidates
            numvotes_next_round = {
                name: nextround_candidates[name] if name not in eliminated_names else 0
                for name in candidates
            }

            # candidate-to-vote-differential
            vote_delta = {
                to_name: numvotes_next_round[to_name] - candidates[to_name] \
                for to_name in candidates
            }
        else:
            nextround_candidates = []
            eliminated_names = []
            vote_delta = {}

        return {
            'nextround_candidates': nextround_candidates,
            'eliminated_names': eliminated_names,
            'vote_delta': vote_delta
        }

    def _weights_for_each_transfer(self, eliminated_names, elected_names, vote_delta):
        """
        If there are multiple candidates transferring their votes, we cannot know
        which candidates contributed to which transfers.
        Our best-effort guess is that they distributed their votes equally to all candidates.
        :param eliminated_names: the names of each eliminated candidate
        :param elected_names: the names of each elected candidate
        :param vote_delta: each candidate's vote differential between this round and the next
        :return: a dict mapping a transferring candidate's name to the weight they contributed
                to the overall transfer. In most cases, there will only be one candidate in
                transferring_candidates and the weight will be a simple 1.0.
        """
        # Names of both eliminated and elected candidates (elected may or may not have surpluses)
        transferring_candidates = eliminated_names + elected_names

        # How many votes are being transferred?
        votes_subtracted = -sum(d for d in vote_delta.values() if d < 0)

        weights = {
            name: -vote_delta[name] / votes_subtracted if votes_subtracted != 0 else 1 \
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

    def _compute_tally_results(self, rounds, round_i):
        """
        Computes the tallyResult, the difference between this round and the next
        :param rounds: The rounds from CSVReader.rounds
        :param round_i: The round on which to compute the tally results

        A lot of magic happens here, so let's walk through it:
        1. Any candidate with # votes greater than the current threshold is elected
        2. Any candidate not present in the next round is eliminated
        3. All elected and eliminated candidates can transfer their votes.
            3a. Elected candidates transfer votes in multi-winner elections when they have surplus
                votes. We do not compute how surplus votes happen, we just look to see if they have
                fewer votes in the next round.
            3b. Eliminated candidates transfer all of their votes.
            3c. If there is more than one candidate transferring votes, we assume they evenly
                distribute their remaining votes to those who are receiving them.
        """
        # Elected candidates is any candidate over the threshold
        candidates = rounds[round_i]['candidates']
        threshold = self._threshold_for_round(rounds, round_i)
        elected_names = [name for name in candidates if candidates[name] >= threshold and name not in self.already_elected]
        self.already_elected.extend(elected_names)

        # Gather data we need about the next round (and how it compares to this round)
        nextround_data = self._what_happens_next_round(rounds, round_i)
        nextround_candidates = nextround_data['nextround_candidates']
        eliminated_names = nextround_data['eliminated_names']
        vote_delta = nextround_data['vote_delta']

        # Generate weights to know how to distribute the transfers
        weights = self._weights_for_each_transfer(eliminated_names, elected_names, vote_delta)

        # Loop over each eliminated or elected candidate and generate the transfers to
        # continuing candidates
        tallyResults = []
        transfer_methods = {
            'eliminated': eliminated_names,
            'elected': elected_names
        }
        for method, names in transfer_methods.items():
            for from_name in names:
                tallyResult = {}
                tallyResult[method] = from_name
                tallyResult['transfers']  = {
                    to_name: vote_delta[to_name] * weights[from_name] \
                    for to_name in nextround_candidates
                }
                tallyResults.append(tallyResult)

        return tallyResults

    def _get_threshold(self, csvData):
        """
        Returns the threshold for the overall election, which doesn't make a lot of sense
        for dynamic-threshold multiwinner elections, but we mark it as just the last
        threshold in the file if the file contains thresholds.
        """
        lastRound = csvData.rounds[-1]
        if lastRound['threshold']:
            return lastRound['threshold']
        else:
            numVotersInLastRound = sum([v for k, v in lastRound['candidates'].items()])
            return numVotersInLastRound / 2.0
