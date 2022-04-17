from dataclasses import dataclass
from typing import List, Optional
import requests
import re

from bs4 import BeautifulSoup
from hazm import Normalizer
import pandas as pd


"""
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

"""


@dataclass
class Quantity:
    full_name: str
    id: str


@dataclass
class Unit:
    quantity: Quantity
    full_name: str
    persian: str
    english: Optional[str] = None

    @staticmethod
    def to_df(units: List["Unit"]) -> pd.DataFrame:
        df = pd.DataFrame(
            [
                (
                    unit.quantity.full_name,
                    unit.quantity.id,
                    unit.full_name,
                    unit.persian,
                    unit.english,
                )
                for unit in units
            ],
            columns=[
                "QuantityName",
                "QuantityId",
                "UnitFullName",
                "Persian",
                "English",
            ],
        )
        return df


class UnitRetriever:
    def __init__(self) -> None:
        self.__session = requests.session()
        self.__session.headers.update(
            {
                "User-Agent": "Mozilla/5.0",
            }
        )
        self.__pattern = re.compile(r"^([^()]+)(\((.+)\))?$")
        self.__normalizer = Normalizer(token_based=True)

    def __get_quantities(self) -> List[Quantity]:
        r = self.__session.get("https://www.bahesab.ir/calc/unit/")
        if r.status_code != 200:
            raise Exception(
                "Failed to get quantities from https://www.bahesab.ir/calc/unit/"
            )
        soup = BeautifulSoup(r.text).select("select.select1 > option")
        return [Quantity(item.get_text(), item["value"]) for item in soup]

    def __get_units(self, quantity: Quantity) -> List[Unit]:
        data = {
            "string_o": f'{{"a":1,"b":"{quantity.id}","c":0,"d":0,"e":0}}',
        }
        r = self.__session.post(
            "https://www.bahesab.ir/cdn/unit/",
            data=data,
            headers=dict(referer="https://www.bahesab.ir/cdn/unit/"),
        )
        if r.status_code != 200:
            raise Exception("Failed to get units from https://www.bahesab.ir/cdn/unit/")

        soup = BeautifulSoup(r.json()["v"]).select("option")
        values = [o["value"] for o in soup]
        units = []
        for unit in values:
            unit = self.__normalizer.normalize(unit)

            mo = self.__pattern.match(unit)
            units.append(Unit(quantity, unit, mo.group(1), mo.group(3)))
        return units

    def retrieve(self) -> List[Unit]:
        quantities = self.__get_quantities()
        units = []
        for quantity in quantities:
            units += self.__get_units(quantity)
        return units


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Retrieve units from bahesab.ir")
    parser.add_argument(
        "--output", "-o", type=str, default="units.csv", help="output file name"
    )

    args = parser.parse_args()

    units = UnitRetriever().retrieve()
    df = Unit.to_df(units)
    df.to_csv(args.output, index=False)
