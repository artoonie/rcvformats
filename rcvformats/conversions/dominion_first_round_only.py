"""
Reads an Dominion XLSX results file, writes to the standard format
"""

import math
import xml.etree.ElementTree as ET

from rcvformats.conversions.base import Converter


class DominionFirstRoundOnlyConverter(Converter):
    """
    Parses the dominion first-round-only file format as exemplified in
    /testdata/inputs/dominionFirstRoundOnly. These are .xml files.
    """

    def _convert_file_object_to_ut(self, file_object):
        element_tree = ET.parse(file_object)
        contest_id_element = element_tree.getroot() \
            .find('{ElectionSummaryReportRPT}tabBatchIdList') \
            .find('{ElectionSummaryReportRPT}TabBatchGroup_Collection') \
            .find('{ElectionSummaryReportRPT}TabBatchGroup') \
            .find('{ElectionSummaryReportRPT}ElectionSummarySubReport') \
            .find('{ElectionSummaryReportRPT}Report') \
            .find('{ElectionSummaryReportRPT}contestList') \
            .find('{ElectionSummaryReportRPT}ContestIdGroup_Collection') \
            .find('{ElectionSummaryReportRPT}ContestIdGroup')

        config = self._parse_config(element_tree, contest_id_element)
        results = self._parse_vote_count(contest_id_element)
        config['threshold'] = self._threshold_from(results)
        urcvt_data = {'config': config, 'results': results}

        return urcvt_data

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
