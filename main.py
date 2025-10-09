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

def main():
    logger.info("Starting...")
    check_inputs(TRANSACTIONS_DIRECTORY, TEST_MIDATA, TEST_STATEMENT)

if __name__ == '__main__':
    main()
