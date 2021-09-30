"""
Reads an Dominion XLSX results file, writes to the standard format
"""
from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.cell.read_only import EmptyCell, ReadOnlyCell

from rcvformats.conversions.base import GenericGuessAtTransferConverter


class DominionConverter(GenericGuessAtTransferConverter):
    """
    Parses the dominion file format as exemplified in /testdata/inputs/dominion
    These are .xlsx files
    """

    # Some constants
    ROUND_LABELS_ROW = 32
    FIRST_CANDIDATE_ON_ROW = 34
    TITLE_CELL = 'A7'
    DATE_CELL = 'A9'
    SEAT_TITLE_CELL = 'A12'
    ROW_AFTER_LAST_CANDIDATE_FOR_INACTIVE_BALLOTS = 4
    ROW_AFTER_LAST_CANDIDATE_FOR_THRESHOLD = 5

    class RoundInfo:  # pylint: disable=too-few-public-methods
        """
        Data for parsing a round:
        Because columns are hapharzadly merged, there is no straightforward mapping from
        round number to the corresponding column. This little struct keeps track of it for us.
        """
        round_num = None
        column = None

    def __init__(self):
        super().__init__()

        # These fields will be filled out as data is loaded

        # The loaded spreadsheet
        self.sheet = None

        # names of each candidate
        self.candidates = None

        # list of RoundInfo, one per round
        self.data_per_round = None

        # Row that has the threshold at each round
        self.row_for_threshold = None

        # Row that has the number of inactive ("non transferrable") ballots at each round
        self.row_for_inactive_ballots = None

    def _convert_file_object_to_ut(self, file_object):
        workbook = load_workbook(file_object)  # note: somehow, readonly is 2x slower
        self.sheet = workbook.active

        config = self._parse_config()
        self.candidates = self._parse_candidates()
        self.row_for_threshold = self._get_row_of_threshold()
        self.row_for_inactive_ballots = self._get_row_of_inactive_ballots()
        self.data_per_round = self._parse_rounds()

        results = self._get_vote_counts_per_candidate()

        urcvt_data = {'config': config, 'results': results}

        workbook.close()

        self._postprocess_remove_last_round_elimination(urcvt_data)
        self._postprocess_set_threshold(urcvt_data)
        return urcvt_data

    def _parse_config(self):
        """
        Returns the URCV config format
        """
        title = self.sheet[self.TITLE_CELL].value
        date_with_time = self.sheet[self.DATE_CELL].value
        date = str(date_with_time.date())
        seat = self.sheet[self.SEAT_TITLE_CELL].value

        config = {
            'contest': title,
            'date': date,
            'office': seat
        }
        return config

    def _parse_rounds(self):
        """
        Rounds are curious - they are separated by a varying number of columns,
        usually 3 except for the first few, where the initial columns have been
        merged seemingly randomly (but in actually: twice in round 1, once in round 2)

        Therefore, this returns a pair of (Round, Column #) to get the column for
        the number of votes in each Round
        """
        col = 3
        data_per_round = []
        max_cols = 1500
        while True:
            cell = self.sheet.cell(self.ROUND_LABELS_ROW, col)
            value = cell.value

            col += 1
            if col >= max_cols:
                raise Exception("This document is not in the correct format..."
                                "or there are more than 500 rounds")

            # Is this a merged cell? If so, ignore it.
            if isinstance(cell, MergedCell):
                continue

            # Have we reached the end of the table?
            if isinstance(cell, EmptyCell):
                break

            if value is None:
                # If we open this as read-only, then None represents a
                # merged cell and we should keep reading
                if isinstance(cell, ReadOnlyCell):
                    continue

                # Otherwise, it represents the end of the table
                break

            num_rounds = len(data_per_round)

            # Are we still in the same round?
            if value == 'Round ' + str(num_rounds):
                continue

            # If not, we must be in the next round. Increment and carry on.
            assert value == 'Round ' + str(num_rounds + 1)
            roundinfo = self.RoundInfo()
            roundinfo.round_num = num_rounds
            roundinfo.column = col - 1
            data_per_round.append(roundinfo)

        assert len(data_per_round) >= 1
        return data_per_round

    def _parse_candidates(self):
        """
        Grabs the list of candidate names from the summary table
        """
        end_of_candidates_marker = 'Continuing Ballots Total'
        max_num_rows = 500
        candidate_names = []
        row = self.FIRST_CANDIDATE_ON_ROW
        while True:
            candidate_name = self.sheet['A' + str(row)].value
            if candidate_name == end_of_candidates_marker:
                break
            if row == max_num_rows:
                raise Exception("This document is not in the correct format..."
                                "or there are more than 500 candidates")
            cell = self.sheet['A' + str(row)]
            name = cell.value
            candidate_names.append(name)
            row += 1
        assert len(candidate_names) >= 1
        return candidate_names

    def _get_row_of_threshold(self):
        """
        Returns row number labeled "Threshold"
        """
        row = self.FIRST_CANDIDATE_ON_ROW
        row += len(self.candidates)
        row += self.ROW_AFTER_LAST_CANDIDATE_FOR_THRESHOLD
        assert self.sheet.cell(row, 1).value == "Threshold"
        return row

    def _get_row_of_inactive_ballots(self):
        """
        Returns row number labeled "Non-Transferrable Total"
        """
        row = self.FIRST_CANDIDATE_ON_ROW
        row += len(self.candidates)
        row += self.ROW_AFTER_LAST_CANDIDATE_FOR_INACTIVE_BALLOTS
        assert self.sheet.cell(row, 1).value == "Non Transferable Total"
        return row

    @classmethod
    def _is_eliminated_color(cls, color):
        """
        Is this cell colored red for elimination?
        Note: only call this if you've checked that the cell is filled solid.
        It may be the case that the cell is red, but not filled, in which case
        it appears white and is not eliminated.
        """
        return color == 'FFFFABAB'

    @classmethod
    def _is_elected_color(cls, color):
        """
        Is this cell colored greed, noting it is elected?
        Note: only call this if you've checked that the cell is filled solid.
        It may be the case that the cell is red, but not filled, in which case
        it appears white and is not eliminated.
        """
        return color == 'FF89CC89'

    def _parse_tally_for_round_at_column(self, col, eliminated_names):
        """ Creates a 'tally' and 'tallyResults' struct for the given round """
        starting_candidate_row = self.FIRST_CANDIDATE_ON_ROW
        tally = {}
        tally_results = []
        for i, name in enumerate(self.candidates):
            if name in eliminated_names:
                continue

            row = starting_candidate_row + i
            cell = self.sheet.cell(row, col)
            vote_count = cell.value
            tally[name] = vote_count

            fill_type = cell.fill.fill_type
            if fill_type is not None:
                bg_color = cell.fill.bgColor.rgb
                if self._is_eliminated_color(bg_color):
                    eliminated_names.add(name)
                    tally_results.append({'eliminated': name})
                elif self._is_elected_color(bg_color):
                    tally_results.append({'elected': name})
                else:
                    # Just make sure we have no rogue colors
                    assert bg_color == '00000000'

        # Add inactive ballots
        tally['Inactive Ballots'] = self.sheet.cell(self.row_for_inactive_ballots, col).value

        return tally, tally_results, eliminated_names

    def _get_vote_counts_per_candidate(self):
        results = []
        eliminated_names = set()
        for round_info in self.data_per_round:
            col = round_info.column
            tally, tally_results, eliminated_names = \
                self._parse_tally_for_round_at_column(col, eliminated_names)
            results.append({
                'round': round_info.round_num + 1,
                'tally': tally,
                'tallyResults': tally_results})
        return results

    @classmethod
    def _postprocess_remove_last_round_elimination(cls, data):
        """
        When there are two candidates left, Dominion marks the loser among them as
        "eliminated", whereas the URCVT format does not.
        Updates data to remove any last-round eliminations
        """
        last_round_tally_results = data['results'][-1]['tallyResults']
        last_round_tally_results = [t for t in last_round_tally_results if 'eliminated' not in t]
        data['results'][-1]['tallyResults'] = last_round_tally_results

    def _postprocess_set_threshold(self, data):
        """
        Set the threshold based on (last round active votes) / (num winners + 1)
        Which is also just listed on the table of per-round info
        """
        last_round_col = self.data_per_round[-1].column
        threshold = self.sheet.cell(self.row_for_threshold, last_round_col).value
        data['config']['threshold'] = threshold
