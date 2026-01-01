from dataclasses import dataclass
import datetime
import copy


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

    def is_interest(self):
        # seems to be this
        return self.amount > 0 and self.kind == "Interest added"

    def precedes(self, other):
        return self.date <= other.date and self.closing_balance == other.closing_balance - other.amount

    def succeeds(self, other):
        return self.date >= other.date and self.closing_balance == other.closing_balance + self.amount

    # TODO: probably only one of copy or redate should be required
    def copy(self):
        return copy.copy(self)

    # TODO: in place?
    def redate(self, new_date):
        redated = copy.copy(self)
        redated.date = new_date
        return redated
