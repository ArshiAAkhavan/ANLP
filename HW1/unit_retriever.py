from dataclasses import dataclass
from functools import partial
import json
from typing import Callable, List, Tuple
import requests
import re

from bs4 import BeautifulSoup
import pandas as pd


'''
TODO: convert

request:
fetch("https://www.bahesab.ir/cdn/unit/", {
  "headers": {
    "Referer": "https://www.bahesab.ir/calc/unit/",
  },
  "body": "string_o=%7B%22a%22%3A2%2C%22b%22%3A%22length%22%2C%22c%22%3A%22%D9%85%D8%AA%D8%B1(m)%22%2C%22d%22%3A%22%DA%A9%DB%8C%D9%84%D9%88%D9%85%D8%AA%D8%B1(km)%22%2C%22e%22%3A%221%22%7D",
  "method": "POST"
});

body: string_o: {"a":2,"b":"unit.quantity.id","c":"source_unit.full_name","d":"target_unit.full_name","e":"1"}

response: {"status":200,"v":"0.001"}

'''

@dataclass
class Quantity:
    full_name: str
    id: str


@dataclass
class Unit:
    quantity: Quantity
    full_name: str
    name: str

    @staticmethod
    def to_df(units: List['Unit']) -> pd.DataFrame:
        df = pd.DataFrame([
            (unit.quantity.full_name, unit.quantity.id, unit.full_name, unit.name)
            for unit in units
        ], columns=['QuantityName', 'QuantityId', 'UnitFullName', 'UnitName'])
        return df


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


class UnitRetriever:

    def __init__(self) -> None:
        self.__session = requests.session()
        self.__session.headers.update({
            'User-Agent': 'Mozilla/5.0',
        })
        self.__first_pattern = re.compile(r'^([^()]*[^()\s])')
        self.__other_pattern = re.compile(r'\s*\(([^()]*[^()\s])\)')
        self.__unit_normalizer = UnitNormalizer()

    def __get_quantities(self) -> List[Quantity]:
        r = self.__session.get('https://www.bahesab.ir/calc/unit/')
        if r.status_code != 200:
            raise Exception('Failed to get quantities from https://www.bahesab.ir/calc/unit/')
        soup = BeautifulSoup(r.text, features='lxml').select('select.select1 > option')
        return [Quantity(item.get_text(), item['value']) for item in soup]

    def __get_units(self, quantity: Quantity) -> List[Unit]:
        data = {
            'string_o': f'{{"a":1,"b":"{quantity.id}","c":0,"d":0,"e":0}}',
        }
        r = self.__session.post('https://www.bahesab.ir/cdn/unit/',
                                data=data,
                                headers=dict(referer='https://www.bahesab.ir/cdn/unit/'))
        if r.status_code != 200:
            raise Exception('Failed to get units from https://www.bahesab.ir/cdn/unit/')

        soup = BeautifulSoup(r.json()['v'], features='lxml').select('option')
        values = [o['value'] for o in soup]
        units = []
        for unit_fullname in values:

            first = self.__first_pattern.match(unit_fullname).group(1)
            units.append(Unit(quantity, unit_fullname, self.__unit_normalizer.normalize(first)))

            if first == 'فوت':
                ###### TOFF ######
                others = self.__other_pattern.findall(unit_fullname)[0].split('-')
            else:
                others = self.__other_pattern.findall(unit_fullname)

            units += [Unit(quantity, unit_fullname, self.__unit_normalizer.normalize(other)) for other in others]

        return units

    def retrieve(self) -> List[Unit]:
        quantities = self.__get_quantities()
        units = []
        for quantity in quantities:
            units += self.__get_units(quantity)
        return units


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve units from bahesab.ir')
    parser.add_argument('--output', '-o', type=str, default='units.csv',
                        help='output file name')

    args = parser.parse_args()

    units = UnitRetriever().retrieve()
    df = Unit.to_df(units)
    df.to_csv(args.output, index=False)
