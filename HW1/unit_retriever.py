from dataclasses import dataclass, field
import os
from typing import List, Tuple
import requests
import re

from bs4 import BeautifulSoup
import pandas as pd

from unit_normalizer import UnitNormalizer


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
    names: List[str]
    id: str
    units: List['Unit'] = field(default_factory=list)

    @staticmethod
    def to_dfs(quantities: List['Quantity']) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        q_df = pd.DataFrame(sum([
            [(q.id, name) for name in q.names] for q in quantities
        ], []), columns=['id', 'name'])
        u_df = pd.DataFrame(sum([
            [(q.id, u.full_name) for u in q.units] for q in quantities
        ], []), columns=['qid', 'id'])
        u_names_df = pd.DataFrame(sum([
            [(u.full_name, name) for name in u.names] for u in sum([q.units for q in quantities], [])
        ], []), columns=['uid', 'name'])
        return q_df, u_df, u_names_df


@dataclass
class Unit:
    full_name: str
    names: List[str] = field(default_factory=list)

    @staticmethod
    def to_df(units: List['Unit']) -> pd.DataFrame:
        df = pd.DataFrame([
            (unit.quantity.full_name, unit.quantity.id, unit.full_name, unit.name)
            for unit in units
        ], columns=['QuantityName', 'QuantityId', 'UnitFullName', 'UnitName'])
        return df


class UnitRetriever:
    __first_pattern = re.compile(r'^([^()]*[^()\s])')
    __other_pattern = re.compile(r'\s*\(([^()]*[^()\s])\)')

    def __init__(self) -> None:
        self.__session = requests.session()
        self.__session.headers.update({
            'User-Agent': 'Mozilla/5.0',
        })
        self.__unit_normalizer = UnitNormalizer()

    @classmethod
    def __split_names(cls, fullname: str) -> List[str]:
        first = cls.__first_pattern.match(fullname).group(1)
        if first == 'فوت':
            ###### TOFF ######
            others = cls.__other_pattern.findall(fullname)[0].split('-')
        else:
            others = cls.__other_pattern.findall(fullname)
        return [first] + others

    def __get_quantities(self) -> List[Quantity]:
        r = self.__session.get('https://www.bahesab.ir/calc/unit/')
        if r.status_code != 200:
            raise Exception('Failed to get quantities from https://www.bahesab.ir/calc/unit/')
        soup = BeautifulSoup(r.text, features='lxml').select('select.select1 > option')
        return [Quantity(self.__split_names(item.get_text()), item['value']) for item in soup]

    def __set_units(self, quantity: Quantity) -> None:
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
        for unit_fullname in values:
            unit = Unit(unit_fullname, [self.__unit_normalizer.normalize(name) for name in self.__split_names(unit_fullname)])
            quantity.units.append(unit)

    def retrieve(self) -> List[Quantity]:
        quantities = self.__get_quantities()
        for quantity in quantities:
            self.__set_units(quantity)
        return quantities


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve units from bahesab.ir')
    parser.add_argument('--directory', '-d', type=str, default='./',
                        help='output directory path')

    args = parser.parse_args()

    quantities = UnitRetriever().retrieve()
    q_df, u_df, u_names_df = Quantity.to_dfs(quantities)

    q_df.to_csv(os.path.join(args.directory, 'quantities.csv'), index=False)
    u_df.to_csv(os.path.join(args.directory, 'units.csv'), index=False)
    u_names_df.to_csv(os.path.join(args.directory, 'unit_names.csv'), index=False)
