import http.client
from dataclasses import dataclass, field
import os
from typing import List, Tuple
import requests
import re
import urllib
from bs4 import BeautifulSoup
import pandas as pd
import json

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
class UnitConversion:
    source: str
    destination: str
    conversion_factor: float

    @staticmethod
    def to_df(units: List['UnitConversion']) -> pd.DataFrame:
        df = pd.DataFrame([
            (unit.source, unit.destination, unit.conversion_factor)
            for unit in units
        ], columns=['Source', 'Destination', 'ConversionFactor'])
        return df


class UnitConversionRetriever:

    def __init__(self, units_path, quantities_path) -> None:
        self.__session = requests.session()
        self.__session.headers.update({
            'User-Agent': 'Mozilla/5.0',
        })
        self.units = pd.read_csv(units_path, index_col=0)
        self.quantities = pd.read_csv(quantities_path, index_col=0)

    def execute(self) -> List[UnitConversion]:
        quantities = self.quantities.index.values
        for quantity in quantities:
            all_rows = self.units[self.units.index.values == quantity]
            base_row = all_rows[:1]
            destination_name = base_row['id'][0]
            for index, row in all_rows.iterrows():
                source_name = row['id']
                print(source_name,destination_name)
                conversion_factor = self.__get_conversion_factor(quantity, source_name, destination_name)
                yield UnitConversion(source_name, destination_name, conversion_factor)

    def __get_conversion_factor(self, quantity, source_name, destination_name) -> float:
        data = {
            'string_o': f'{{"a":2,"b":"{quantity}","c":"{source_name}","d":"{destination_name}","e":"1"}}',
        }
        conn = http.client.HTTPSConnection("www.bahesab.ir")
        data = urllib.parse.urlencode(data)
        headers = {
            'Referer': 'https://www.bahesab.ir/cdn/unit/',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        conn.request("POST", "/cdn/unit/", data, headers)
        res = conn.getresponse()
        result = json.loads(res.read().decode("utf-8"))
        return float(result['v'])


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Retrieve units from bahesab.ir',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--output', '-o', type=str, default='./unit_conversion.csv',
                        help='output path')
    parser.add_argument('--units', '-u', default='./units.csv')
    parser.add_argument('--quantities', '-q', default='./quantities.csv')

    args = parser.parse_args()

    unit_conversion_retriever = UnitConversionRetriever(args.units, args.quantities)
    unit_conversions = unit_conversion_retriever.execute()
    df = UnitConversion.to_df(unit_conversions)
    df.to_csv(args.output)
