from typing import Tuple
from parsi_io.modules.number_extractor import NumberExtractor
from pprint import pprint as print
from dataclasses import dataclass
from typing import Tuple, List
import re

extractor = NumberExtractor()


@dataclass
class Output:
    quiantity: str
    amount: int
    unit: str
    item: str
    marker: str
    span: Tuple[int, int]


units = ["متر بر ثانیه", "گرم"]
unit_regex = re.compile(f'({"|".join(units)})')


NUMBER_TRASH_MAGIC = "⌠"
UNIT_TRASH_MAGIC = "⌡"
RESERVED_TRASH_MAGIC = "Ж"
ANOTHER_RESERVED_TRASH_MAGIC = "Д"

num_patterns = f"{NUMBER_TRASH_MAGIC}+"
unit_patterns = f"{UNIT_TRASH_MAGIC}+"
word_patterns = "[\u0600-\u06ff]+"

NUMBER_PATTERN_NAME = "number"
UNIT_PATTERN_NAME = "unit"
ITEM_PATTERN_NAME = "item"
patterns = [
    f"(?P<{NUMBER_PATTERN_NAME}>{num_patterns})\s+(?P<{UNIT_PATTERN_NAME}>{unit_patterns})+\s+(?P<{ITEM_PATTERN_NAME}>{word_patterns})",
    f"(?P<{NUMBER_PATTERN_NAME}>{num_patterns})\s+(?P<{UNIT_PATTERN_NAME}>{unit_patterns})+\s+(?P<{ITEM_PATTERN_NAME}>{word_patterns})",
]

pattern_regex = [re.compile(pattern) for pattern in patterns]


def normalize_numbers(matn: str) -> str:
    for num in extractor.run(matn):
        print(num)
        for i in range(num["span"][0], num["span"][1]):
            matn = matn[0:i] + NUMBER_TRASH_MAGIC + matn[i + 1 :]
    return matn


def normalize_units(matn: str) -> str:
    for match in unit_regex.finditer(matn):
        span = match.span()
        matn = (
            matn[: span[0]] + UNIT_TRASH_MAGIC * (span[1] - span[0]) + matn[span[1] :]
        )
    return matn


@dataclass
class ES:
    amount: Tuple[int, int]
    unit: Tuple[int, int]
    item: Tuple[int, int]

    def __repr__(self):
        return f"{self.amount}|{self.unit}|{self.item}"
    
    def __eq__(self,other):
        return self.amount==other.amount and self.unit==other.unit and self.item==other.item
    
    def __hash__(self):
        return hash((self.amount,self.unit,self.item))



def extract_patterns(matn: str) -> List[ES]:
    results = set()
    for regex in pattern_regex:
        for match in regex.finditer(matn):
            res = ES(
                amount=match.span(NUMBER_PATTERN_NAME),
                unit=match.span(UNIT_PATTERN_NAME),
                item=match.span(ITEM_PATTERN_NAME),
            )
            results.add(res)
    return results


matn = "دیروز با مهدی رفتم ۲ گرم کالباس خریدم و با هم با سرعت ۲۵ متر بر ثانیه دویدیم"
matn_2 = normalize_numbers(matn)
matn_3 = normalize_units(matn_2)
print(matn)
print(matn_2)
print(matn_3)
print(extract_patterns(matn_3))
