import argparse
import logging
import os
import sys

from nationwide_parser.statement import StatementParseError, read_nationwide_file
from nationwide_parser.account import Account


# parse args
arg_parser = argparse.ArgumentParser(
        description="Extract transactions from exported Nationwide statements.",
        )
arg_parser.add_argument("-v", "--verbose", action="store_true")
arg_parser.add_argument("infiles", nargs="*")

argv = arg_parser.parse_args()

# setup
logger = logging.getLogger("main")
if argv.verbose:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
else:
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def main():
    logger.info("Starting...")

    statements = []
    for arg in argv.infiles:
        if os.path.isdir(arg):
            new_filenames = [os.path.join(arg, f) for f in os.listdir(arg)]
            new_filepaths = [f for f in new_filenames if not os.path.isdir(f)]
            statements.extend(new_filepaths)
        elif os.path.isfile(arg):
            statements.append(arg)
        else:
            logger.warning(f"{arg} is not a file")
    if statements == []:
        logger.info("Nothing to do")
        sys.exit(0)

    logger.debug(f"Found statements {statements}")

    # collect observed accounts
    num_statements = len(statements)
    successful_reads = 0
    accounts = {}

    for statement in statements:
        try:
            account_name, transactions = read_nationwide_file(statement)
            successful_reads += 1
            logger.info(f"Read {len(transactions)} transactions for account {account_name}")
            if account_name in accounts:
                accounts[account_name].add_unique_transactions(transactions)
            else:
                accounts[account_name] = Account(account_name, transactions)
        except StatementParseError as e:
            logger.warning(e)

    if successful_reads == 0:
        logger.info(f"Could not parse any input files.")
        return

    if successful_reads == num_statements:
        msg = f"Parsed all {num_statements} files successfully, with the following results:"
    else:
        msg = f"Parsed {successful_reads}/{num_statements} files successfully, with the following results:"
    logger.info(msg)

    for x in accounts:
        logger.info(f"Account {x}: {len(accounts[x].transactions)} {'complete' if accounts[x].all_transactions_are_continuous() else 'incomplete'} transactions from {accounts[x].transactions[0].date} to {accounts[x].transactions[-1].date}")

if __name__ == "__main__":
    main()
