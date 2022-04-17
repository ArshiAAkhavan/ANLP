import re

NUMBER_TRASH_MAGIC = "⌠"
UNIT_TRASH_MAGIC = "⌡"
RESERVED_TRASH_MAGIC = "Ж"
ANOTHER_RESERVED_TRASH_MAGIC = "Д"


NUMBER_PATTERN_NAME = "number"
UNIT_PATTERN_NAME = "unit"
ITEM_PATTERN_NAME = "item"

num_pattern = f"(?P<{NUMBER_PATTERN_NAME}>{NUMBER_TRASH_MAGIC}+)"
unit_pattern = f"(?P<{UNIT_PATTERN_NAME}>{UNIT_TRASH_MAGIC}+)"
item_pattern = f"(?P<{ITEM_PATTERN_NAME}>[\u0600-\u06ff]+)"
patterns = [
    rf"{num_pattern}\s+{unit_pattern}\s+{item_pattern}",
]

unit_overlap_regex = re.compile(
    rf'({UNIT_TRASH_MAGIC}+)(\s+)(?:{UNIT_TRASH_MAGIC})')
pattern_regex = [re.compile(pattern) for pattern in patterns]
