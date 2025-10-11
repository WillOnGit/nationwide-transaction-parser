import csv
import os
import logging
import sys

from statements import Midata, Nationwide


# setup
logger = logging.getLogger("natpar")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def read_nationwide_file(file):
    file_basename = os.path.basename(file)
    logger.debug(f'Reading file "{file_basename}"')

    # Nationwide exports files encoded with ISO-8859-1, using CRLF terminators
    f = open(file, encoding="latin_1")

    # for now, skip through lines until we hit an identifying CSV header
    statement_formats = [ Midata, Nationwide ]
    statement_format = None
    while (statement_format is None):
        line = f.readline()
        if line == '': # EOF
            logger.warning(f"Could not detect a statement format for {file_basename}")
            return None
        for fmt in statement_formats:
            if line.strip() == fmt.header:
                statement_format = fmt
                logger.debug(f"Format for {file_basename} detected as {statement_format}")
                break

    # parse rest of file as CSV
    c = csv.reader(f)

    transactions = []
    for row in c:
        logger.debug(row)
        # only applicable to midata
        if len(row) == 0:
            break
        transaction = statement_format.parse_transaction(row)
        logger.debug(transaction)
        transactions.append(transaction)

    logger.info(f'Parsed {len(transactions)} transactions from file "{file_basename}"')
    f.close()
    return transactions

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

    for statement_dir in statement_dirs:
        statements = os.listdir(statement_dir)
        for statement in statements:
            read_nationwide_file(os.path.join(statement_dir, statement))
    logger.info("Done")

if __name__ == "__main__":
    main()
