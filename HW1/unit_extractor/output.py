from dataclasses import dataclass
from typing import Tuple


@dataclass
class RawOutput:
    amount: Tuple[int, int]
    unit: Tuple[int, int]
    item: Tuple[int, int]
    span: Tuple[int, int]

    def __repr__(self):
        return f"{self.amount}|{self.unit}|{self.item}|{self.span}"

    def __eq__(self, other):
        return (
            self.amount == other.amount
            and self.unit == other.unit
            and self.item == other.item
            and self.span == other.span
        )

    def __hash__(self):
        return hash((self.amount, self.unit, self.item, self.span))


@dataclass
class ValidOutput:
    quantity: str
    amount: int
    unit: str
    item: str
    marker: str
    span: Tuple[int, int]
