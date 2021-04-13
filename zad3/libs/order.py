from dataclasses import dataclass
from typing import Iterable, Tuple

@dataclass
class Order:
    order: Iterable

    def __hash__(self):
        return hash(self.order)

    def __eq__(self, other):
        return self.order == other.order

class NpOrder(Order):
    def __hash__(self):
        return hash(self.order.tostring())

    def __eq__(self, val):
        return (self.order == val.order).all()
