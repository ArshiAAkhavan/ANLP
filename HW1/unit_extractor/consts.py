import re

NUMBER_TRASH_MAGIC = "⌠"
UNIT_TRASH_MAGIC = "⌡"
QUANTIFIER_TRASH_MAGIC = "Ж"
ADVERB_TRASH_MAGIC = "Д"
STOP_TRASH_MAGIC = "И"


NUMBER_GROUP_NAME = "number"
UNIT_GROUP_NAME = "unit"
ITEM_GROUP_NAME = "item"
ADVERB_GROUP_NAME = "adverb"
QUANTIFIER_GROUP_NAME = "quantifier"


num_regex = f"(?P<{NUMBER_GROUP_NAME}>{NUMBER_TRASH_MAGIC}+)"
unit_regex = f"(?P<{UNIT_GROUP_NAME}>{UNIT_TRASH_MAGIC}+)"
item_regex = f"(?P<{ITEM_GROUP_NAME}>[\u0600-\u06ff]+)"
quantity_regex = f"(?P<{QUANTIFIER_GROUP_NAME}>{QUANTIFIER_TRASH_MAGIC}+)"
adverb_regex = f"(?P<{ADVERB_GROUP_NAME}>{ADVERB_TRASH_MAGIC}+)"
stopword_regex = f"({STOP_TRASH_MAGIC}+)"
stopword_optional_regex = f"(\s+{STOP_TRASH_MAGIC}+\s+|\s+)"
white_space_regex = r"(\s+)"


pattern_map = {
    "N": num_regex,
    "U": unit_regex,
    "I": item_regex,
    " ": white_space_regex,
    "Q": quantity_regex,
    "A": adverb_regex,
    "S": stopword_regex,
    "s": stopword_optional_regex,
}

patterns_raw = [
    "N U I",
    "IsQ N U",
    "Q N U",
    "Q A",
]


patterns = []
for p in patterns_raw:
    pattern = ""
    for identifier in p:
        pattern = pattern + pattern_map[identifier]
    patterns.append(pattern)


unit_overlap_regex = re.compile(rf"({UNIT_TRASH_MAGIC}+)(\s+)(?:{UNIT_TRASH_MAGIC})")
pattern_regex = [re.compile(pattern) for pattern in patterns]
