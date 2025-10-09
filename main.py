import csv
import os
import logging
import sys


# setup
logger = logging.getLogger("natpar")
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

try:
    from env import TEST_MIDATA, TEST_STATEMENT, TRANSACTIONS_DIRECTORY
except ImportError:
    logger.critical("Could not import from env.py; please see the README")
    sys.exit(1)

def check_inputs(input_dir, midata, statement):
    failed = False

    if not os.path.isdir(input_dir):
        logger.critical(f"{input_dir} is not a directory!")
        sys.exit(1)
    if not os.path.isfile(os.path.join(input_dir, midata)):
        logger.critical(f"{midata} is not a file!")
        failed = True
    if not os.path.isfile(os.path.join(input_dir, statement)):
        logger.critical(f"{statement} is not a file!")
        failed = True

    if failed:
        sys.exit(1)
    else:
        logger.info("All inputs are correct; ready to go")

def read_nationwide_file(file):
    logger.info(f"Reading first five lines of file {file}")

    # Nationwide exports files encoded with ISO-8859-1, using CRLF terminators
    f = open(file, encoding="latin_1")
    c = csv.reader(f)

    n = 0
    for line in c:
        if n >= 5:
            return
        print(line)
        n += 1

    f.close()

def main():
    logger.info("Starting...")
    check_inputs(TRANSACTIONS_DIRECTORY, TEST_MIDATA, TEST_STATEMENT)
    read_nationwide_file(os.path.join(TRANSACTIONS_DIRECTORY, TEST_STATEMENT))
    read_nationwide_file(os.path.join(TRANSACTIONS_DIRECTORY, TEST_MIDATA))
    logger.info("Done")

if __name__ == "__main__":
    main()
