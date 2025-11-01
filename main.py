import argparse
import logging
import os
import sys

from nationwide_parser.statement import read_nationwide_file
from nationwide_parser.account import Account


# parse args
arg_parser = argparse.ArgumentParser(
        description="Extract transactions from exported Nationwide statements.",
        )
arg_parser.add_argument("-v", "--verbose", action="store_true")
arg_parser.add_argument("directories", nargs="*")

argv = arg_parser.parse_args()

# setup
logger = logging.getLogger("main")
if argv.verbose:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def main():
    logger.info("Starting...")

    statement_dirs = []
    for arg in argv.directories:
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
            logger.info(f"Read {len(transactions)} transactions for account {account_name}")
            if account_name in accounts:
                accounts[account_name].add_unique_transactions(transactions)
            else:
                accounts[account_name] = Account(account_name, transactions)

    logger.info("Parsed all files successfully, with the following results:")
    for x in accounts:
        logger.info(f"Account {x}: {len(accounts[x].transactions)} {'complete' if accounts[x].all_transactions_are_continuous() else 'incomplete'} transactions from {accounts[x].transactions[0].date} to {accounts[x].transactions[-1].date}")
    logger.info("Done")

if __name__ == "__main__":
    main()
