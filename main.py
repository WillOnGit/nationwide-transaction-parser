import logging
import os
import sys

from nationwide_parser.statement import read_nationwide_file
from nationwide_parser.account import Account


# setup
logger = logging.getLogger("natpar")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

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
    accounts = {}

    for statement_dir in statement_dirs:
        statements = os.listdir(statement_dir)
        for statement in statements:
            account_name, transactions = read_nationwide_file(os.path.join(statement_dir, statement))
            logger.info(f"Read {len(transactions)} transactions from account {account_name}")
            if account_name in accounts:
                accounts[account_name].add_unique_transactions(transactions)
            else:
                accounts[account_name] = Account(account_name, transactions)

    logger.info(f"Unique observed accounts: {list(accounts)} ({len(list(accounts))})")
    for x in accounts:
        logger.info(f"Final window for {x}: {accounts[x].transactions[0].date} -> {accounts[x].transactions[-1].date}")
    logger.info("Done")

if __name__ == "__main__":
    main()
