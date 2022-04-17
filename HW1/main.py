from typing import Tuple
from parsi_io.modules.number_extractor import NumberExtractor
from pprint import pprint as print
from dataclasses import dataclass
from typing import Tuple, List
import re
extractor = NumberExtractor()


@dataclass
class Output:
    type_: str
    amount: int
    unit: str
    item: str
    marker: str
    span: Tuple[int, int]


units = ['متر بر ثانیه', 'گرم']
unit_regex=re.compile(f'({"|".join(units)})')


NUMBER_TRASH_MAGIC = "⌠"
UNIT_TRASH_MAGIC   = "⌡"
RESERVED_TRASH_MAGIC = "Ж"
ANOTHER_RESERVED_TRASH_MAGIC = "Д"

num_patterns=f"{NUMBER_TRASH_MAGIC}+"
unit_patterns=f"{UNIT_TRASH_MAGIC}+"
amount_patterns="[\]+"

patterns = [("")]



def normalize_numbers(matn: str) -> str:
    for num in extractor.run(matn):
        print(num)
        for i in range(num["span"][0],num["span"][1]):
            matn=matn[0:i] + NUMBER_TRASH_MAGIC + matn[i+1:]
    return matn

def normalize_units(matn:str):
    for match in unit_regex.finditer(matn):
        span=match.span()
        matn=matn[:span[0]]+ UNIT_TRASH_MAGIC*(span[1]-span[0]) + matn[span[1]:]
    return matn

matn = 'دیروز با مهدی رفتم ۲ گرم کالباس خریدم و با هم با سرعت ۲۵ متر بر ثانیه دویدیم'
matn_2=normalize_numbers(matn)
matn_3=normalize_units(matn_2)
print(matn)
print(matn_2)
print(matn_3)