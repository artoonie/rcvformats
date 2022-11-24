"""
Reads an Dominion TXT results file, used by Alaska since they have consistently
failed to publish the easier-to-read Dominion JSON file.
"""
from datetime import datetime
import io

from rcvformats.conversions.base import CouldNotConvertException
from rcvformats.conversions.base import GenericGuessAtTransferConverter


class DominionTxtConverter(GenericGuessAtTransferConverter):
    """
    Parses the dominion file format as exemplified in /testdata/inputs/dominion.txt
    """

    def _convert_file_object_to_ut(self, file_object):
        # Note: don't use context manager here; we don't want to close the file_object,
        # which TextIOWrapper's context manager will do
        decoded_buffer = io.TextIOWrapper(file_object, encoding='utf-16-le')

        self._skip_lines(decoded_buffer, 1)
        line2 = self._get_next_line_exploded(decoded_buffer)

        # Line 2: date
        date = line2[3]
        date = date.strip()
        try:
            # This format is used by alaska but it is not universal
            # Format: 8-Nov-22
            dateparts = date.split('-')
            dateday = int(dateparts[0])
            datemonth = datetime.strptime(dateparts[1], "%b").strftime("%m")
            dateyear = datetime.strptime(dateparts[2], "%y").strftime("%Y")
            date = f"{dateyear}-{datemonth:02d}-{dateday:02d}"
        except ValueError:
            # After 2022-11-24, remove this hardcoded value once we figure out what
            # format alaska will actually use
            date = "2022-11-08"

        self._skip_lines(decoded_buffer, 2)

        # Line 5: the first section is the title
        line5 = self._get_next_line_exploded(decoded_buffer)
        title = line5[0]

        # Skip 5 ilnes to get to the list of rounds
        self._skip_lines(decoded_buffer, 5)

        config = {
            'contest': title,
            'date': date
        }

        results = self._process_rounds(decoded_buffer)

        # We're done with the buffer - we can detach now, to avoid gc
        # from closing the file.
        decoded_buffer.detach()

        urcvt_data = {
            'config': config,
            'results': results
        }
        self.postprocess_remove_last_round_elimination(urcvt_data)
        self.postprocess_use_standard_irv_threshold(urcvt_data)

        return urcvt_data

    @classmethod
    def _process_rounds(cls, decoded_buffer):
        all_rounds = []
        curr_round = None
        round_num = 1

        def _make_empty_round(round_num):
            return {'round': round_num, 'tally': {}, 'tallyResults': []}

        curr_round = _make_empty_round(round_num)
        while True:
            try:
                line = cls._get_next_line_exploded(decoded_buffer)
            except StopIteration:
                break

            # We're looking for a line that looks like:
            # State\tRound X\n"Candidate Name"\t"Num Votes"
            if len(line) >= 4 and line[1].startswith("Round ") and line[2].startswith("\""):
                # First thing we check: are we in the same Round # as we expect to be?
                # If not, commit the last round and create a new one
                if int(line[1].split("Round ")[1]) != round_num:
                    all_rounds.append(curr_round)
                    round_num += 1
                    curr_round = _make_empty_round(round_num)

                candidate_name = cls._name_strip(line[2])
                num_votes = float(line[3].strip("\"").replace(",", ""))
                if num_votes == 0:
                    continue
                curr_round['tally'][candidate_name] = num_votes
            else:
                elected_name = cls._who_is_eliminated_or_elected('is elected', line)
                if elected_name:
                    curr_round['tallyResults'].append({'elected': elected_name})

                eliminated_name = cls._who_is_eliminated_or_elected('is eliminated', line)
                if eliminated_name:
                    curr_round['tallyResults'].append({
                        'eliminated': eliminated_name,
                        'transfers': {}
                    })

                xfer_data = cls._get_transfer_data(line)
                if xfer_data:
                    cls._add_transfers(curr_round, xfer_data)

        # Commit final round, if it's not empty
        if curr_round and curr_round['tally']:
            all_rounds.append(curr_round)

        return all_rounds

    @classmethod
    def _skip_lines(cls, decoded_buffer, num_line_to_skip):
        for _ in range(num_line_to_skip):
            next(decoded_buffer)

    @classmethod
    def _get_next_line_exploded(cls, decoded_buffer):
        line = next(decoded_buffer)
        if not line:
            return None
        return line.split('\t')

    @classmethod
    def _who_is_eliminated_or_elected(cls, elim_or_elect_text, line):
        """
        These lines have box 17 which looks like, including the quotes:
        "Palin, Sarah is eliminated because the candidate was not elected in the last round."

        returns None if nobody was
        """
        if len(line) < 17:
            return None

        cell = line[17]
        if elim_or_elect_text not in cell:
            return None

        name = cell.split(elim_or_elect_text)[0]
        return cls._name_strip(name)

    @classmethod
    def _get_transfer_data(cls, line):
        """
        These lines have cells 20-22 which looks like, including the quotes:
        20: "From"
        21: "To"
        22: Num Votes

        returns None if not relevant
        """
        if len(line) < 23:
            return None

        transfer_text = line[18]
        if not transfer_text.startswith("\"Elimination transfer for candidate"):
            return None

        from_name = cls._name_strip(line[20])
        to_name = cls._name_strip(line[21])
        n_votes = float(line[22])

        if to_name == from_name:
            # We don't care about negative transfers to ourself
            return None

        if to_name in ('Overvotes', "Exhausted"):
            # We only care about valid votes going forward
            return None

        return {'from': from_name, 'to': to_name, 'n_votes': n_votes}

    @classmethod
    def _name_strip(cls, name):
        """ Strips quotes first, then spaces """
        return name.strip("\"").strip()

    @classmethod
    def _add_transfers(cls, curr_round, xfer_data):
        for tally_result in curr_round['tallyResults']:
            if 'eliminated' not in tally_result:
                continue
            if tally_result['eliminated'] != xfer_data['from']:
                continue
            tally_result['transfers'][xfer_data['to']] = xfer_data['n_votes']
            return

        raise CouldNotConvertException(f"Couldn't find {xfer_data['from']} to transfer votes to")
