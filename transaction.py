from dataclasses import dataclass
import datetime


@dataclass
class Transaction:
    date: datetime.date
    amount: int # pennies
    kind: str
    description: str
    closing_balance: int
