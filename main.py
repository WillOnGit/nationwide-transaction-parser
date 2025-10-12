import logging
import os
import sys

from statements import read_nationwide_file


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

    for statement_dir in statement_dirs:
        statements = os.listdir(statement_dir)
        for statement in statements:
            read_nationwide_file(os.path.join(statement_dir, statement))
    logger.info("Done")

if __name__ == "__main__":
    main()
