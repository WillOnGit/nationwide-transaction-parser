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
    logger.info(f'Reading file "{file_basename}"')

    # Nationwide exports files encoded with ISO-8859-1, using CRLF terminators
    f = open(file, encoding="latin_1")

    # for now, skip through lines until we hit an identifying CSV header
    # TODO: handle case where no header reached
    while (a := f.readline()):
        if a.strip() == Midata.header:
            transaction_parser = Midata.parse_transaction
            break
        elif a.strip() == Nationwide.header:
            transaction_parser = Nationwide.parse_transaction
            break

    # parse rest of file as CSV
    c = csv.reader(f)
    n = 0

    for row in c:
        # only applicable to midata
        if len(row) == 0:
            break
        logger.debug(transaction_parser(row))
        n += 1
    logger.info(f'Parsed {n} transactions from file "{file_basename}"')

    f.close()

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
