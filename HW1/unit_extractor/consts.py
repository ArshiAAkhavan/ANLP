import re

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

