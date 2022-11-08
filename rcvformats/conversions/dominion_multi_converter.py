"""
Reads an Dominion XML file containing many contests.
"""

import math
import json
from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET


class DominionMultiConverter():  # pylint: disable=too-few-public-methods
    """
    Parses the dominion first-round-only file format as exemplified in
    testdata/inputs/dominion-multi-converter.xml, which contains many elections.
    """
    @classmethod
    def explode_to_files(cls, file_object):
        """
        Given the XML format with multiple elections,
        explodes into many files, and returns a dictionary of titles to NamedTemporaryFiles.
        """
        element_tree = ET.parse(file_object)
        contest_id_groups = element_tree.getroot() \
            .find('{ElectionSummaryReportRPT}tabBatchIdList') \
            .find('{ElectionSummaryReportRPT}TabBatchGroup_Collection') \
            .find('{ElectionSummaryReportRPT}TabBatchGroup') \
            .find('{ElectionSummaryReportRPT}ElectionSummarySubReport') \
            .find('{ElectionSummaryReportRPT}Report') \
            .find('{ElectionSummaryReportRPT}contestList') \
            .find('{ElectionSummaryReportRPT}ContestIdGroup_Collection') \
            .findall('{ElectionSummaryReportRPT}ContestIdGroup')

        output = {}
        for contest_id_element in contest_id_groups:
            config = cls._parse_config(element_tree, contest_id_element)
            results = cls._parse_vote_count(contest_id_element)
            config['threshold'] = cls._threshold_from(results)
            urcvt_data = {'config': config, 'results': results}

            # Hack - we only want the contests with >2 candidates + write-in
            if len(results[0]['tally']) <= 3:
                continue

            # pylint: disable=consider-using-with
            temp_file = NamedTemporaryFile(suffix=".json", mode='r+')
            json.dump(urcvt_data, temp_file)
            temp_file.flush()
            output[config['contest']] = temp_file

        return output

    @classmethod
    def _parse_config(cls, element_tree, contest_id_element):
        config = {}
        config['date'] = element_tree.getroot() \
            .find('{ElectionSummaryReportRPT}Title') \
            .find('{ElectionSummaryReportRPT}Report') \
            .get('Textbox9')
        # Remove the timestamp from the date
        config['date'] = config['date'][:10]
        config['contest'] = contest_id_element.get('contestId')

        return config

    @classmethod
    def _parse_vote_count(cls, contest_id_element):
        tally = {}
        candidates = contest_id_element \
            .find('{ElectionSummaryReportRPT}CandidateResults') \
            .find('{ElectionSummaryReportRPT}Report') \
            .find('{ElectionSummaryReportRPT}Tablix1') \
            .find('{ElectionSummaryReportRPT}chGroup_Collection')
        for candidate in candidates.findall('{ElectionSummaryReportRPT}chGroup'):
            candidate_data = candidate.find('{ElectionSummaryReportRPT}candidateNameTextBox4')
            name = candidate_data.get('candidateNameTextBox4')
            num_votes = candidate_data.find('{ElectionSummaryReportRPT}Textbox13').get('vot8')
            tally[name] = float(num_votes)

        return [{
            "round": 1,
            "tally": tally,
            "tallyResults": []
        }]

    @classmethod
    def _threshold_from(cls, results):
        total = sum(results[0]['tally'].values())
        return math.floor(total / 2 + 1)
