from dataclasses import dataclass
import datetime


@dataclass
class Transaction:
    date: datetime.date
    amount: int # pennies
    kind: str
    description: str
    closing_balance: int

    def is_equivalent(self, other):
        return self.date == other.date and self.amount == other.amount and self.closing_balance == other.closing_balance
