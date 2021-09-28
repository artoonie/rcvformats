import json
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.cell.read_only import EmptyCell, ReadOnlyCell

from rcvformats.conversions.base import GenericGuessAtTransferConverter

class DominionConverter(GenericGuessAtTransferConverter):
    """
    Parses the dominion file format as exemplified in /testdata/inputs/dominion
    These are .xlsx files
    """
    def _convert_file_object_to_ut(self, file_object):
        tf = 'testdata/inputs/dominion/las-cruces-mayor.xlsx'
        wb = load_workbook(filename=tf)  # note: somehow, readonly is 2x slower
        self.sheet = wb.active

        config = self.parse_config()
        self.candidates = self.parse_candidates()
        self.roundinfo = self.parse_rounds()

        results = self.get_vote_counts_per_candidate()

        urcvt_data = {'config': config, 'results': results}

        wb.close()

        self.postprocess_remove_last_round_elimination(urcvt_data)
        return urcvt_data

    def parse_config(self):
        title = self.sheet['A7'].value
        dateWithTime = self.sheet['A9'].value
        date = str(dateWithTime.date())
        seat = self.sheet['A12'].value

        config = {
            'contest': title,
            'date': date,
            'office': seat
        }
        return config

    def parse_rounds(self):
        """
        Rounds are curious - they are separated by a varying number of columns,
        usually 3 except for the first few, where the initial columns have been
        merged seemingly randomly (but in actually: twice in round 1, once in round 2)

        Therefore, this returns a pair of (Round, Column #) to get the column for
        the number of votes in each Round
        """
        col = 3
        roundinfo = []
        max_cols = 1500
        while True:
            cell = self.sheet.cell(32, col)
            value = cell.value

            col += 1
            if col >= 1500:
                raise Exception("This document is not in the correct format..."\
                                "or there are more than 500 rounds");

            # Is this a merged cell? If so, ignore it.
            if isinstance(cell, MergedCell):
                continue

            # Have we reached the end of the table?
            if isinstance(cell, EmptyCell):
                break

            # Also a merged-cell check, but for when read_only is True
            if value is None:
                if isinstance(cell, ReadOnlyCell):
                    continue
                else:
                    break

            num_rounds = len(roundinfo)

            # Are we still in the same round?
            if value == 'Round ' + str(num_rounds):
                continue

            # If not, we must be in the next round. Increment and carry on.
            assert value == 'Round ' + str(num_rounds+1)
            roundinfo.append((num_rounds, col-1))

        assert len(roundinfo) >= 1
        return roundinfo

    def parse_candidates(self):
        """
        Grabs the list of candidate names from the summary table
        """
        end_of_candidates_marker = 'Continuing Ballots Total'
        max_num_rows = 500
        candidate_names = []
        row = 34  # first candidate is on row 34
        while True:
            candidate_name = self.sheet['A'+str(row)].value
            if candidate_name == end_of_candidates_marker:
                break
            if row == max_num_rows:
                raise Exception("This document is not in the correct format..."\
                                    "or there are more than 500 candidates")
            cell = self.sheet['A'+str(row)]
            name = cell.value
            candidate_names.append(name)
            row += 1
        assert len(candidate_names) >= 1
        return candidate_names

    def is_eliminated_color(self, color):
        """
        Is this cell colored red for elimination?
        Note: only call this if you've checked that the cell is filled solid.
        It may be the case that the cell is red, but not filled, in which case
        it appears white and is not eliminated.
        """
        return color == 'FFFFABAB'

    def is_elected_color(self, color):
        """
        Is this cell colored greed, noting it is elected?
        Note: only call this if you've checked that the cell is filled solid.
        It may be the case that the cell is red, but not filled, in which case
        it appears white and is not eliminated.
        """
        return color == 'FF89CC89'

    def parse_tally_for_round_at_column(self, col, eliminated_names):
        """ Creates a 'tally' and 'tallyResults' struct for the given round """
        num_candidates = len(self.candidates)
        starting_candidate_row = 34
        tally = {}
        tallyResults = []
        for i in range(len(self.candidates)):
            name = self.candidates[i]
            if name in eliminated_names:
                continue

            row = starting_candidate_row + i
            cell = self.sheet.cell(row, col)
            vote_count = cell.value
            tally[name] = vote_count

            fill_type = cell.fill.fill_type
            if fill_type is not None:
                bg_color = cell.fill.bgColor.rgb
                if self.is_eliminated_color(bg_color):
                    eliminated_names.add(name)
                    tallyResults.append({'eliminated': name})
                elif self.is_elected_color(bg_color):
                    tallyResults.append({'elected': name})
                else:
                    # Just make sure we have no rogue colors
                    assert bg_color == '00000000'

        return tally, tallyResults, eliminated_names

    def get_vote_counts_per_candidate(self):
        results = []
        eliminated_names = set()
        for (round_num, col) in self.roundinfo:
            tally, tallyResults, eliminated_names = \
                    self.parse_tally_for_round_at_column(col, eliminated_names)
            results.append({
                'round': round_num + 1,
                'tally': tally,
                'tallyResults': tallyResults})
        return results

    def postprocess_remove_last_round_elimination(self, data):
        """
        When there are two candidates left, Dominion marks the loser among them as
        "eliminated", whereas the URCVT format does not.
        """
        last_round_tally_results = data['results'][-1]['tallyResults']
        last_round_tally_results = [t for t in last_round_tally_results if 'eliminated' not in t]
        data['results'][-1]['tallyResults'] = last_round_tally_results


tf1 = 'DominionTestFile.xlsx'
tf2 = 'testdata/inputs/dominion/las-cruces-mayor.xlsx'

converter = DominionConverter()
output = converter.convert_to_ut_and_validate(tf2)

with open('test.json', 'w') as f:
    json.dump(output, f, indent=2)
