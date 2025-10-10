from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    date: date
    amount: int # pennies
    kind: str
    description: str
    closing_balance: int
