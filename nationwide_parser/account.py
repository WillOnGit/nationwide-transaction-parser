import logging


logger = logging.getLogger(__name__)

class InconsistentTransactionsError(Exception):
    """Raised when two transactions cannot be reconciled"""

    pass

class Account:
    """An account consisting of a name and a chronological list of
    Transactions"""

    def __init__(self, name, transactions=[]):
        self.name = name
        self.transactions = transactions

    def __str__(self):
        return self.name

    """Add only new transactions to account, returning how many were
    added"""
    def add_unique_transactions(self, new_transactions):
        if new_transactions is self.transactions:
            logger.warning("Attempt to insert own transactions into self detected; aborting")
            return 0

        if new_transactions == []:
            logger.debug("new_transactions empty; nothing to do")
            return 0

        logger.debug(f"New transactions window: {new_transactions[0].date} -> {new_transactions[-1].date} ")

        if self.transactions == []:
            logger.debug(f"{self.name} had no transactions; adding all {len(new_transactions)} new transactions")
            self.transactions = new_transactions
            return len(new_transactions)

        # prep
        old_transactions_length = len(self.transactions)
        old_transactions_start = self.transactions[0].date
        new_transactions_length = len(new_transactions)
        new_transactions_start = new_transactions[0].date

        unique_transaction_indexes = [] # list of tuples (index of self.transactions where to insert, index of transaction in new_transactions)
        old_i = new_i = 0

        # skip through early non-overlapping transactions
        if old_transactions_start < new_transactions_start:
            while self.transactions[old_i].date < new_transactions_start:
                old_i += 1
            logger.debug(f"Skipped over {old_i} earlier old transactions")
        elif new_transactions_start < old_transactions_start:
            while new_transactions[new_i].date < old_transactions_start:
                unique_transaction_indexes.insert(0, (0, new_i))
                new_i += 1
            logger.debug(f"Marked {new_i} earlier new transactions for insertion")

        # compare overlapping transactions
        # loop ends when we run out of old or new transactions to compare
        while new_i < new_transactions_length and old_i < old_transactions_length:
            if new_transactions[new_i].is_equivalent(self.transactions[old_i]):
                # transactions match, nothing to do
                old_i += 1
                new_i += 1
                logger.debug("Skipping duplicate transaction")
                continue
            elif new_transactions[new_i].date < self.transactions[old_i].date:
                # this new transaction fills in a gap
                unique_transaction_indexes.insert(0, (old_i, new_i))
                new_i += 1
                logger.debug("Marked an overlapping new transaction for insertion")
            else:
                # transactions on the same date should agree
                raise InconsistentTransactionsError(f"Inconsistent transaction data! New transaction {new_transactions[new_i]} conflicts with {self.transactions[old_i]}")

        # if there are any leftover new transactions, they come after any existing ones
        for x in range(new_i, new_transactions_length):
            unique_transaction_indexes.insert(0, (old_transactions_length, x))
            logger.debug("Marked a later new transaction for insertion")

        # append new transactions and exit
        # apply in reverse order so higher indexes aren't corrupted by inserting before
        for x in unique_transaction_indexes:
            self.transactions.insert(x[0], new_transactions[x[1]])
        logger.debug(f"Merged {len(unique_transaction_indexes)}/{new_transactions_length} transactions into account {self.name}")
        return len(unique_transaction_indexes)
