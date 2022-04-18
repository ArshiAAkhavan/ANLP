
from functools import partial
import json
import re
from typing import Callable, List, Tuple


class UnitNormalizer:
    Converter = Callable[[str], str]
    def __init__(self, conf_path: str = 'unit_normalization_conf.json') -> None:
        conf = self.__load_conf(conf_path)
        self.__delimiter = conf['delimiter']
        prefixes = conf['prefixes']
        replacements = conf['replacements']
        self.__handle_prefix = self.__converter(rf'(?P<prefix>(^|\W)({"|".join(prefixes)}))(?P<suffix>\w+.*)$',
                                                rf'\g<prefix>{self.__delimiter}\g<suffix>')
        self.__handle_replacements = self.__replacer(replacements)

    @staticmethod
    def __load_conf(conf_path: str) -> dict:
        with open(conf_path, 'r') as f:
            return json.load(f)

    @staticmethod
    def __convert(pattern: re.Pattern, repl: str, text: str) -> str:
        while (newtext := pattern.sub(repl, text)) != text:
            text = newtext
        return text

    @classmethod
    def __converter(cls, pattern: str, repl: str) -> 'UnitNormalizer.Converter':
        return partial(cls.__convert, re.compile(pattern, re.IGNORECASE), repl)

    def __replacer(self, replacements: List[Tuple[str, str]]) -> 'UnitNormalizer.Converter':
        replacements: List[Tuple[re.Pattern, str]] = [
            (re.compile(pattern, re.IGNORECASE), repl.replace(r'\D', self.__delimiter))
            for pattern, repl in replacements
        ]
        def replacer(text: str) -> str:
            for pattern, repl in replacements:
                text = pattern.sub(repl, text)
            return text
        return replacer

    def normalize(self, text: str) -> str:
        text = self.__handle_prefix(text)
        text = self.__handle_replacements(text)
        return text
