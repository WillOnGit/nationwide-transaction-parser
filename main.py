import logging
import os
import sys

from statements import read_nationwide_file


# setup
logger = logging.getLogger("natpar")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def add_unique_transactions(accounts, account, new_transactions):
    if new_transactions == []:
        logger.debug("new_transactions empty; nothing to do")
        return

    logger.info(f"New transactions window: {new_transactions[0].date} -> {new_transactions[-1].date} ")
    if account not in accounts:
        logger.info(f"initialising {account} with {len(new_transactions)} new transactions")
        accounts[account] = new_transactions
        return

    # prep
    old_transactions = accounts[account] # an alias to make things legible

    old_transactions_length = len(accounts[account])
    old_transactions_start = accounts[account][0].date
    new_transactions_length = len(new_transactions)
    new_transactions_start = new_transactions[0].date

    unique_transaction_indexes = []
    old_i = new_i = 0

    # skip through early non-overlapping transactions
    if old_transactions_start < new_transactions_start:
        while old_transactions[old_i].date < new_transactions_start:
            old_i += 1
        logger.debug(f"Skipped over {old_i} earlier old transactions")
    elif new_transactions_start < old_transactions_start:
        while new_transactions[new_i].date < old_transactions_start:
            unique_transaction_indexes.insert(0, (new_i, 0))
            new_i += 1
        logger.debug(f"Marked {new_i} earlier new transactions for insertion")

    # compare overlapping transactions
    # loop ends when we run out of old or new transactions to compare
    while new_i < new_transactions_length and old_i < old_transactions_length:
        if new_transactions[new_i].is_equivalent(old_transactions[old_i]):
            # transactions match, nothing to do
            old_i += 1
            new_i += 1
            continue
        elif new_transactions[new_i].date < old_transactions[old_i].date:
            # this new transaction fills in a gap
            unique_transaction_indexes.insert(0, (new_i, old_i))
            new_i += 1
        else:
            # transactions on the same date should agree
            raise ValueError(f"Inconsistent transaction data! New transaction {new_transactions[new_i]} conflicts with {old_transactions[old_i]}")

    # if there are any leftover new transactions, they come after any existing ones
    for x in range(new_i, new_transactions_length):
        unique_transaction_indexes.insert(0, (x, old_transactions_length))

    # append new transactions and exit
    # apply in reverse order so higher indexes aren't corrupted by inserting before
    for x in unique_transaction_indexes:
        old_transactions.insert(x[0], new_transactions[x[1]])
    logger.info(f"Merged {len(unique_transaction_indexes)} into account {account}")
    return

def main():
    logger.info("Starting...")

    statement_dirs = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            statement_dirs.append(arg)
        else:
            logger.warning(f"Skipping {arg} as it is not a directory")
    if statement_dirs == []:
        logger.info("Nothing to do")
        sys.exit(0)

    # collect observed accounts
    # dictionary mapping account name (arbitrary string) -> sorted list of transactions
    accounts = {}

    for statement_dir in statement_dirs:
        statements = os.listdir(statement_dir)
        for statement in statements:
            account, transactions = read_nationwide_file(os.path.join(statement_dir, statement))
            logger.info(f"Read {len(transactions)} transactions from account {account}")
            add_unique_transactions(accounts, account, transactions)
    logger.info(f"Unique observed accounts: {list(accounts)} ({len(list(accounts))})")
    for x in accounts:
        logger.info(f"Final window for {x}: {accounts[x][0].date} -> {accounts[x][-1].date}")
    logger.info("Done")

if __name__ == "__main__":
    main()
