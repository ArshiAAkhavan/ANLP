from pprint import pprint as print
from typing import List, Set

from parsi_io.modules.number_extractor import NumberExtractor
from unit_extractor.consts import (ITEM_PATTERN_NAME, NUMBER_PATTERN_NAME,
                                   NUMBER_TRASH_MAGIC, UNIT_PATTERN_NAME,
                                   UNIT_TRASH_MAGIC, pattern_regex, unit_regex)
from unit_extractor.output import RawOutput, ValidOutput


class UnitExtractor:
    def __init__(self):
        self.num_extractor = NumberExtractor()

    def _normalize_numbers(self, matn: str) -> str:
        for num in self.num_extractor.run(matn):
            for i in range(num["span"][0], num["span"][1]):
                matn = matn[0:i] + NUMBER_TRASH_MAGIC + matn[i + 1:]
        return matn

    def _normalize_units(self, matn: str) -> str:
        for match in unit_regex.finditer(matn):
            span = match.span()
            matn = (
                matn[: span[0]] + UNIT_TRASH_MAGIC *
                (span[1] - span[0]) + matn[span[1]:]
            )
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

    def _generate_outputs(self, matn: str, raw_outputs: Set[RawOutput]) -> List[ValidOutput]:
        results = []
        for raw in raw_outputs:
            unit = matn[raw.unit[0]: raw.unit[1]]
            amount = matn[raw.amount[0]: raw.amount[1]]
            item = matn[raw.item[0]: raw.item[1]]
            marker = matn[raw.span[0]: raw.span[1]]
            o = ValidOutput(
                quantity=get_quantity_from_unit(unit),
                unit=unit,
                amount=amount,
                item=item,
                span=raw.span,
                marker=marker,
            )
            results.append(o)
        return results

    def run(self, matn: str) -> List[ValidOutput]:
        m1 = self._normalize_numbers(matn)
        m2 = self._normalize_units(m1)
        raw_outputs = self._extract_patterns(m2)
        valid_outputs = self._generate_outputs(matn, raw_outputs)
        return valid_outputs


def get_quantity_from_unit(unit: str) -> str:
    # TODO
    return "متر"

