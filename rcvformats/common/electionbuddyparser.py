"""
Helper class for loading Electionbuddy CSVs
"""


class ElectionBuddyData:
    """
    Structure to hold the raw data read from the file.
    Parses the data directly into a simple format.
    Used for both conversion and schema validation.
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
            round_text = self.read_line_as_str()
            if not round_text.startswith("Round"):
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
                threshold_str = line[len('Threshold: '):]
                threshold = float(threshold_str)
            else:
                assert line.strip() == ''
                break

        # Check for newline
        line = self.read_line_as_str()
        assert line.strip() == ''

        return {'candidates': candidates,
                'threshold': threshold}
