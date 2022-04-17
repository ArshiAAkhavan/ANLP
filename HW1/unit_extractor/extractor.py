import re
from typing import List, Set

from parsi_io.modules.number_extractor import NumberExtractor
from unit_extractor.consts import (ITEM_PATTERN_NAME, NUMBER_PATTERN_NAME,
                                   NUMBER_TRASH_MAGIC, UNIT_PATTERN_NAME,
                                   UNIT_TRASH_MAGIC, pattern_regex,
                                   unit_overlap_regex)
from unit_extractor.output import RawOutput, ValidOutput
from unit_retriever import UnitRetriever


class UnitExtractor:
    def __init__(self):
        self.num_extractor = NumberExtractor()
        self.units = UnitRetriever().retrieve()
        unit_names = [unit.persian.strip() for unit in self.units]
        self.unit_regex = re.compile(
            f'({"|".join(unit_names)})')

    def _normalize_numbers(self, matn: str) -> str:
        for num in self.num_extractor.run(matn):
            start = num["span"][0]
            end = num["span"][1]
            length = end-start
            matn = matn[0:start]+NUMBER_TRASH_MAGIC*length+matn[end:]
        return matn

    def _normalize_units(self, matn: str) -> str:
        for match in self.unit_regex.finditer(matn):
            span = match.span()
            start = span[0]
            end = span[1]
            length = end-start
            matn = matn[: start] + UNIT_TRASH_MAGIC * length + matn[end:]

        for match in unit_overlap_regex.finditer(matn):
            span = match.span(2)
            start = span[0]
            end = span[1]
            length = end-start
            matn = matn[: start] + UNIT_TRASH_MAGIC * length + matn[end:]
        print(matn)
        return matn

    def _extract_patterns(self, matn: str) -> List[RawOutput]:
        results = set()
        for regex in pattern_regex:
            for match in regex.finditer(matn):
                res = RawOutput(
                    amount=match.span(NUMBER_PATTERN_NAME),
                    unit=match.span(UNIT_PATTERN_NAME),
                    item=match.span(ITEM_PATTERN_NAME),
                    span=match.span(),
                )
                results.add(res)
        return results

    def _generate_outputs(
        self, matn: str, raw_outputs: Set[RawOutput]
    ) -> List[ValidOutput]:
        results = []
        for raw in raw_outputs:
            unit = matn[raw.unit[0]: raw.unit[1]]
            amount = matn[raw.amount[0]: raw.amount[1]]
            item = matn[raw.item[0]: raw.item[1]]
            marker = matn[raw.span[0]: raw.span[1]]
            o = ValidOutput(
                quantity=self.get_quantity_from_unit(unit),
                unit=unit,
                amount=amount,
                item=item,
                span=raw.span,
                marker=marker,
            )
            results.append(o)
        return results

    def get_quantity_from_unit(self, unit_name: str) -> str:
        for unit in self.units:
            if unit.persian.strip() == unit_name.strip():
                return unit.quantity.full_name
        return ""

    def run(self, matn: str) -> List[ValidOutput]:
        m1 = self._normalize_numbers(matn)
        m2 = self._normalize_units(m1)
        raw_outputs = self._extract_patterns(m2)
        valid_outputs = self._generate_outputs(matn, raw_outputs)
        return valid_outputs
