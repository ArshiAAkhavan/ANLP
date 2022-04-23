from dataclasses import dataclass, field
import os
from typing import List, Tuple
import requests
import re

import regex
from bs4 import BeautifulSoup
import pandas as pd

from unit_normalizer import UnitNormalizer


@dataclass
class Quantity:
    names: List[str]
    id: str
    units: List['Unit'] = field(default_factory=list)

    @staticmethod
    def to_dfs(quantities: List['Quantity']) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        q = pd.DataFrame(sum([
            [(q.id, name) for name in q.names] for q in quantities
        ], []), columns=['id', 'name'])
        u = pd.DataFrame(sum([
            [(q.id, u.full_name, u.conversion_factor) for u in q.units] for q in quantities
        ], []), columns=['qid', 'id', 'conversion_factor'])
        u_names = pd.DataFrame(sum([
            [(u.full_name, name) for name in u.names] for u in sum([q.units for q in quantities], [])
        ], []), columns=['uid', 'name'])
        return q, u, u_names

    @staticmethod
    def from_dfs(q: pd.DataFrame, u: pd.DataFrame, u_names: pd.DataFrame) -> List['Quantity']:
        return [Quantity(
            [name for name in q[q.id == qid].name.values],
            qid,
            units=[Unit(
                uid,
                names=[name for name in u_names[u_names.uid == uid].name.values],
                conversion_factor=cf
            ) for uid, cf in u.loc[u.qid == qid, ['id', 'conversion_factor']].values]
        ) for qid in q.id.unique()]


@dataclass
class Unit:
    full_name: str
    names: List[str] = field(default_factory=list)
    conversion_factor: float = 1.0


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
        result = [first] + others
        if 'سانتیگراد' in result:
            result.append('درجهسانتیگراد')
        return result

    def __get_quantities(self) -> List[Quantity]:
        r = self.__session.get('https://www.bahesab.ir/calc/unit/')
        if r.status_code != 200:
            raise Exception('Failed to get quantities from https://www.bahesab.ir/calc/unit/')
        soup = BeautifulSoup(r.text, features='lxml').select('select.select1 > option')
        return [Quantity(self.__split_names(item.get_text()), item['value']) for item in soup]

    def __set_conversion_factor(self, quantity: Quantity, unit: Unit) -> None:
        if len(quantity.units) == 0:
            return

        data = {
            'string_o': f'{{"a":2,"b":"{quantity.id}","c":"{quantity.units[0].full_name}","d":"{unit.full_name}","e":"1"}}',
        }
        r = self.__session.post('https://www.bahesab.ir/cdn/unit/',
                                data=data,
                                headers=dict(referer='https://www.bahesab.ir/cdn/unit/'))
        if r.status_code != 200:
            raise Exception('Failed to get conversion factor from https://www.bahesab.ir/cdn/unit/')

        unit.conversion_factor = float(r.json()['v'])

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
            self.__set_conversion_factor(quantity, unit)
            quantity.units.append(unit)

    def retrieve(self) -> List[Quantity]:
        quantities = self.__get_quantities()
        for quantity in quantities:
            self.__set_units(quantity)
        return quantities


class UnitPatternEscaper:
    pattern = regex.compile(r'(?V1)\((?:[^)(]+|(?R))*+\)') # https://stackoverflow.com/a/35271017/10635586

    def __call__(self, unit_name: str) -> str:
        return self.pattern.sub('', unit_name)


def is_persian_char(char: str) -> bool:
    return ord('؀') <= ord(char) <= ord('ۿ')


class PrefixPrepender:

    def __init__(self, u_df: pd.DataFrame, uname_df: pd.DataFrame) -> None:
        self.unit_pattern_escaper = UnitPatternEscaper()
        self.unit_normalizer = UnitNormalizer()
        is_prefix = uname_df['uid'].isin(u_df[u_df['qid'] == 'pishvand']['id'])
        self.uname_df = uname_df[uname_df['name'].str[0].apply(is_persian_char) & ~is_prefix]
        self.puname_df = uname_df[uname_df['name'].str[0].apply(is_persian_char) & is_prefix]
        self.uid_by_name = {self.unit_pattern_escaper(name): uid for uid, name in self.uname_df.itertuples(index=False)}
        self.q_by_uid = {uid: (qid, cfactor) for qid, uid, cfactor in u_df.itertuples(index=False)}
        self.prefix_regex = re.compile(rf'^({"|".join(self.puname_df["name"].values)})')

    def prepend(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        extra_u = dict(qid=[], id=[], conversion_factor=[])
        extra_uname = dict(uid=[], name=[])
        for uid, name in self.uname_df.itertuples(index=False):
            for puid, pname in self.puname_df.itertuples(index=False):
                if self.prefix_regex.match(name) is None and (new_uname := self.unit_pattern_escaper(f'{pname}{name}')) not in self.uid_by_name:
                    new_uname = self.unit_normalizer.normalize(new_uname)
                    new_uid = f'{puid}-{uid}'
                    qid, cfactor = self.q_by_uid[uid]
                    new_cfactor = self.q_by_uid[puid][1] / self.q_by_uid['یونی(u)'][1] * cfactor
                    extra_u['qid'].append(qid)
                    extra_u['id'].append(new_uid)
                    extra_u['conversion_factor'].append(new_cfactor)
                    extra_uname['uid'].append(new_uid)
                    extra_uname['name'].append(new_uname)
        u_df = pd.DataFrame(extra_u)
        uname_df = pd.DataFrame(extra_uname)
        return u_df, uname_df


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve units from bahesab.ir',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--directory', '-d', type=str, default='./',
                        help='output directory path')
    parser.add_argument('--no-prepend', action='store_true',
                        help='do not prepend prefixes')

    args = parser.parse_args()

    quantities = UnitRetriever().retrieve()
    q, u, u_names = Quantity.to_dfs(quantities)

    if not args.no_prepend:
        u_df, u_names_df = PrefixPrepender(u, u_names).prepend()
        u = pd.concat([u, u_df], sort=False)
        u_names = pd.concat([u_names, u_names_df], sort=False)

    os.makedirs(args.directory, exist_ok=True)
    q.to_csv(os.path.join(args.directory, 'quantities.csv'), index=False)
    u.to_csv(os.path.join(args.directory, 'units.csv'), index=False)
    u_names.to_csv(os.path.join(args.directory, 'unit_names.csv'), index=False)
