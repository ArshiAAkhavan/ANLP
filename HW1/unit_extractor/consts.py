import re

NUMBER_TRASH_MAGIC = "⌠"
UNIT_TRASH_MAGIC = "⌡"
RESERVED_TRASH_MAGIC = "Ж"
ANOTHER_RESERVED_TRASH_MAGIC = "Д"


NUMBER_GROUP_NAME = "number"
UNIT_GROUP_NAME = "unit"
ITEM_GROUP_NAME = "item"

num_regex = f"(?P<{NUMBER_GROUP_NAME}>{NUMBER_TRASH_MAGIC}+)"
unit_regex = f"(?P<{UNIT_GROUP_NAME}>{UNIT_TRASH_MAGIC}+)"
item_regex = f"(?P<{ITEM_GROUP_NAME}>[\u0600-\u06ff]+)"
white_space_regex = r"(\s+)"

pattern_map = {"N": num_regex, "U": unit_regex, "I": item_regex, " ": white_space_regex}

patterns_raw = ["N U I",
        ]


patterns = []
for p in patterns_raw:
    pattern = ""
    for identifier in p:
        pattern = pattern + pattern_map[identifier]
    patterns.append(pattern)


unit_overlap_regex = re.compile(rf"({UNIT_TRASH_MAGIC}+)(\s+)(?:{UNIT_TRASH_MAGIC})")
pattern_regex = [re.compile(pattern) for pattern in patterns]
