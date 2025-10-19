import csv
import datetime
import logging
import os
import re

from transaction import Transaction


class StatementReader():
    def __init__(self, header, account_regex, parse_raw_transaction, order_raw_transactions):
        self.header = header
        self._transaction_fields = header.count(",") + 1
        self._account_regex = re.compile(account_regex)
        self._parse_raw_transaction = parse_raw_transaction
        self._order_transactions = order_raw_transactions

    def get_account_description(self, row):
        match = self._account_regex.search(row)
        if match:
            return match.group(1)
        else:
            return None

    def parse_transaction(self, row):
        if len(row) != self._transaction_fields:
            raise ValueError(f"Expected {self._transaction_fields} fields but received {len(row)} instead")

        return self._parse_raw_transaction(row)

    def order(self, results):
        return self._order_transactions(results)

# field parsers
def _parse_monetary_amount(money_string):
    # check for £ with optional +/-
    if money_string[0] == "£":
        sign = 1
        amount_index = 1
    elif money_string[0] == "+" and money_string[1] == "£":
        sign = 1
        amount_index = 2
    elif money_string[0] == "-" and money_string[1] == "£":
        sign = -1
        amount_index = 2
    else:
        raise ValueError("Could not detect £ sign; aborting")

    # parse number
    remove_full_stop = str.maketrans({".":""})
    magnitude = int(money_string.translate(remove_full_stop)[amount_index:])

    # return positive/negative integer
    return sign * magnitude

# Midata
_MIDATA_HEADER = '"Date","Type","Merchant/Description","Debit/Credit","Balance"'

def _parse_midata_date(date_string):
    # allow exceptions to crash the program while we test input data
    # expects: 13/06/2025
    day = int(date_string[0:2])
    month = int(date_string[3:5])
    year = int(date_string[6:])

    return datetime.date(year, month, day)

def _midata_parse_transaction(row):
    date = _parse_midata_date(row[0])
    amount = _parse_monetary_amount(row[3])
    kind = row[1]
    description = row[2]
    closing_balance = _parse_monetary_amount(row[4])
    return Transaction(date, amount, kind, description, closing_balance)

Midata = StatementReader(_MIDATA_HEADER, r'"Account Number:","([^"]+)"', _midata_parse_transaction, lambda x : x[::-1])


# Nationwide
_NATIONWIDE_HEADER = '"Date","Transaction type","Description","Paid out","Paid in","Balance"'

def _parse_nationwide_date(date_string):
    # allow exceptions to crash the program while we test input data
    # expects: 13 Jun 2025
    day = int(date_string[0:2])
    year = int(date_string[7:])

    # awkward
    month_mappings = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
            }
    month_string = date_string[3:6]
    month = month_mappings[month_string]

    return datetime.date(year, month, day)

def _nationwide_parse_transaction(row):
    date = _parse_nationwide_date(row[0])
    kind = row[1]
    description = row[2]
    closing_balance = _parse_monetary_amount(row[5])

    # hmm not a fan of this tbh
    if row[3] == "":
        amount = _parse_monetary_amount(row[4])
    elif row[4] == "":
        amount = -1 * _parse_monetary_amount(row[3])
    else:
        raise ValueError("Paid out/Paid in could not be parsed")

    return Transaction(date, amount, kind, description, closing_balance)

    return Transaction()

Nationwide = StatementReader(_NATIONWIDE_HEADER, r'"Account Name:","([^"]+)"', _nationwide_parse_transaction, lambda x : x)

# use this
logger = logging.getLogger("natpar")

def read_nationwide_file(file):
    file_basename = os.path.basename(file)
    logger.debug(f'Reading file "{file_basename}"')

    # Nationwide exports files encoded with ISO-8859-1, using CRLF terminators
    f = open(file, encoding="latin_1")

    # check file not empty
    line = f.readline()
    if line == '': # EOF
        logger.warning(f'"{file_basename}" is empty')
        f.close()
        return None

    # try getting account name from first line only
    statement_formats = [ Midata, Nationwide ]
    statement_format = None

    for fmt in statement_formats:
        account_name = fmt.get_account_description(line)
        if account_name is not None:
            statement_format = fmt
            logger.debug(f'Detected format {statement_format} for "{file_basename}"')
            break

    if statement_format is None:
        logger.warning(f'Could not detect a statement format for "{file_basename}"')
        f.close()
        return None

    # skip through lines until we hit the CSV header
    while (True):
        line = f.readline()
        if line == '': # EOF
            logger.warning(f'Could not detect start of transaction data for "{file_basename}"')
            f.close()
            return None
        elif line.strip() == statement_format.header:
            logger.debug(f'Detected start of transaction data for "{file_basename}"')
            break

    # parse rest of file as CSV
    c = csv.reader(f)

    transactions = []
    for row in c:
        logger.debug(row)
        # only applicable to midata
        if len(row) == 0:
            break
        try:
            transaction = statement_format.parse_transaction(row)
            logger.debug(transaction)
            transactions.append(transaction)
        except ValueError:
            f.close()
            raise
        except:
            f.close()
            logger.warning("An unexpected error occurred!")
            raise

    logger.info(f'Parsed {len(transactions)} transactions from file "{file_basename}"')
    f.close()
    return (account_name, statement_format.order(transactions))
