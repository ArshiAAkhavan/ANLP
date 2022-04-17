from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class RawOutput:
    amount: Optional[Tuple[int, int]]
    unit: Optional[Tuple[int, int]]
    quan: Optional[Tuple[int, int]]
    item: Optional[Tuple[int, int]]
    span: Optional[Tuple[int, int]]

    def __repr__(self):
        return f"{self.amount}|{self.unit}|{self.item}|{self.span}"

    def __eq__(self, other):
        return (
            self.amount == other.amount
            and self.unit == other.unit
            and self.item == other.item
            and self.span == other.span
            and self.quan == other.quan
        )

    def __hash__(self):
        return hash((self.amount, self.unit, self.item, self.span, self.quan))


@dataclass
class ValidOutput:
    quantity: str
    amount: int
    unit: str
    item: str
    marker: str
    span: Tuple[int, int]
