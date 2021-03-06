import re
from typing import List, Set, Tuple
import warnings
from hazm import Normalizer
import codecs
import logging

import pandas as pd
from parsi_io.modules.number_extractor import NumberExtractor
from unit_extractor.consts import (
    ADVERB_TRASH_MAGIC,
    ITEM_GROUP_NAME,
    NUMBER_GROUP_NAME,
    NUMBER_TRASH_MAGIC,
    QUANTIFIER_GROUP_NAME,
    QUANTIFIER_TRASH_MAGIC,
    UNIT_GROUP_NAME,
    UNIT_TRASH_MAGIC,
    STOP_TRASH_MAGIC,
    WORD_SURROUNDING_REGEX,
    pattern_regex,
    unit_overlap_regex,
)
from unit_extractor.output import RawOutput, ValidOutput
from unit_retriever import UnitPatternEscaper


class UnitExtractor:
    def __init__(self):
        self.num_extractor = NumberExtractor()
        self.unit_pattern_escaper = UnitPatternEscaper()

        self.q_df = pd.read_csv("quantities.csv")
        self.u_df = pd.read_csv("units.csv")
        self.uname_df = pd.read_csv("unit_names.csv")

        unit_names = self.uname_df['name'].tolist()
        unit_names.sort(key=lambda x: len(self.unit_pattern_escaper(x)), reverse=True)
        self.unit_regex = re.compile(f'{WORD_SURROUNDING_REGEX}({"|".join(unit_names)}){WORD_SURROUNDING_REGEX}')

        quantifiers = self.q_df['name'].tolist()
        quantifiers.sort(key=len, reverse=True)
        self.quantifier_regex = re.compile(f'{WORD_SURROUNDING_REGEX}({"|".join(quantifiers)}){WORD_SURROUNDING_REGEX}')

        adverbs = ["بسیار سنگین","بسیار سبک","بسیار کم","بسیار زیاد","زیادی","کمی","بسیار","سبک","سنگین","زیاد", "کم"]
        self.adverb_regex = re.compile(f'({"|".join(adverbs)})')

        self.stopwords=[Normalizer().normalize(x.strip()) for x in codecs.open('stopwords.txt','r','utf-8').readlines()]
        self.stopword_regex = re.compile(f'({"|".join(self.stopwords)})')

    def _tag_numbers(self, matn: str) -> str:
        try:
            numbers = self.num_extractor.run(matn)
        except Exception as e:
            warnings.warn(f'Number extraction failed: {e}')
            return matn
        for num in numbers:
            start = num["span"][0]
            end = num["span"][1]
            length = end - start
            matn = matn[0:start] + NUMBER_TRASH_MAGIC * length + matn[end:]
        return matn

    @staticmethod
    def _tag_by_name(matn: str, regex: re.Pattern, tag: str) -> str:
        for match in regex.finditer(matn):
            span = match.span(1)
            start = span[0]
            end = span[1]
            length = end - start
            matn = matn[:start] + tag * length + matn[end:]
        return matn

    def _tag_quantifier(self, matn: str) -> str:
        return self._tag_by_name(matn, self.quantifier_regex, QUANTIFIER_TRASH_MAGIC)

    def _tag_adverb(self, matn: str) -> str:
        return self._tag_by_name(matn, self.adverb_regex, ADVERB_TRASH_MAGIC)
    
    def _tag_stopwords(self, matn: str) -> str:
        matn_splited=matn.split(" ")
        for i,word in enumerate(matn_splited):
            if word in self.stopwords:
                matn_splited[i]=STOP_TRASH_MAGIC*len(word)
        return " ".join(matn_splited)

    def _tag_units(self, matn: str) -> str:
        matn = self._tag_by_name(matn, self.unit_regex, UNIT_TRASH_MAGIC)

        for match in unit_overlap_regex.finditer(matn):
            span = match.span(2)
            start = span[0]
            end = span[1]
            length = end - start
            matn = matn[:start] + UNIT_TRASH_MAGIC * length + matn[end:]
        return matn

    def _extract_patterns(self, matn: str) -> List[RawOutput]:
        results_unchecked = set()
        for regex in pattern_regex:
            for match in regex.finditer(matn):
                try:
                    amount = match.span(NUMBER_GROUP_NAME)
                except IndexError:
                    amount = None

                try:
                    unit = match.span(UNIT_GROUP_NAME)
                except IndexError:
                    unit = None

                try:
                    quan = match.span(QUANTIFIER_GROUP_NAME)
                except IndexError:
                    quan = None

                try:
                    item = match.span(ITEM_GROUP_NAME)
                except IndexError:
                    item = None

                span = match.span()

                res = RawOutput(
                    amount=amount, unit=unit, item=item, span=span, quan=quan
                )
                results_unchecked.add(res)
        
        results=[]
        for target in results_unchecked:
            flag=1
            for res in results_unchecked:
                if res==target:
                    continue
                if res.span[0]<=target.span[0] and target.span[1]<=res.span[1]:
                   flag=0
                   break 
            if flag:
                results.append(target)
        return results

    def _generate_outputs(
        self, matn: str, raw_outputs: Set[RawOutput]
    ) -> List[ValidOutput]:
        results = []
        for raw in raw_outputs:
            unit = matn[raw.unit[0] : raw.unit[1]] if raw.unit else ""
            quan = matn[raw.quan[0] : raw.quan[1]] if raw.quan else ""
            item = matn[raw.item[0] : raw.item[1]] if raw.item else ""
            marker = matn[raw.span[0] : raw.span[1]]

            try:
                if raw.amount:
                    amount_raw = matn[raw.amount[0] : raw.amount[1]]
                    amount = self.num_extractor.run(amount_raw)[0]["value"]
                else:
                    amount = ""
            except:
                logging.warning(f"couldn't convert {amount_raw}...")
                continue
                

            quantity = self.get_quantity_from_unit(unit)
            if not quantity or len(quantity) == 0:
                quantity = quan

            o = ValidOutput(
                quantity=quantity,
                unit=unit,
                amount=amount,
                item=item,
                span=raw.span,
                marker=marker,
            )
            results.append(o)
        return results

    def get_quantity_and_proper_unit_from_unit_name(self, unit_name: str) -> Tuple[str, str, str]:
        if not unit_name:
            return '', '', ''

        uid = self.uname_df[self.uname_df['name'].apply(lambda regex: re.match(rf'^{regex}$', unit_name) is not None)][
            'uid'].tolist()
        if not uid:
            warnings.warn(f'Unit name "{unit_name}" not found in unit_names.csv')
            return '', '', ''

        uid = uid[0]
        qid = self.u_df[self.u_df['id'] == uid]['qid'].tolist()
        qid = qid[0]
        qnames = self.q_df[self.q_df['id'] == qid]['name'].tolist()
        return qnames[0], qid, uid

    def get_quantity_from_unit(self, unit_name: str) -> str:
        return self.get_quantity_and_proper_unit_from_unit_name(unit_name)[0]

    def run(self, matn: str) -> List[ValidOutput]:
        m1 = self._tag_numbers(matn)
        m2 = self._tag_units(m1)
        m3 = self._tag_quantifier(m2)
        m4 = self._tag_adverb(m3)
        m5 = self._tag_stopwords(m4)
        raw_outputs = self._extract_patterns(m5)
        valid_outputs = self._generate_outputs(matn, raw_outputs)
        return valid_outputs
