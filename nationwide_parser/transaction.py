from dataclasses import dataclass
import datetime


@dataclass
class Transaction:
    date: datetime.date
    amount: int # pennies
    kind: str
    description: str
    closing_balance: int

    def __str__(self):
        if self.amount < 0:
            str_preposition = "to"
        else:
            str_preposition = "from"

        absolute_amount = abs(self.amount)

        if absolute_amount < 100:
            display_amount = f"{absolute_amount}p"
        else:
            display_amount = f"£{absolute_amount//100}.{absolute_amount % 100:02}"

        return f"{display_amount} {str_preposition} {self.description} on {self.date}"

    def is_equivalent(self, other):
        return self.date == other.date and self.amount == other.amount and self.closing_balance == other.closing_balance
