from datetime import date
import os
import csv
import logging

from transaction import Transaction


class StatementReader():
    def __init__(self, header, parse_raw_transaction):
        self.header = header
        self._transaction_fields = header.count(",") + 1
        self._parse_raw_transaction = parse_raw_transaction

    def parse_transaction(self, row):
        if len(row) != self._transaction_fields:
            raise ValueError(f"Expected {self._transaction_fields} fields but received {len(row)} instead")

        return self._parse_raw_transaction(row)

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

    return date(year, month, day)

def _midata_parse_transaction(row):
    date = _parse_midata_date(row[0])
    amount = _parse_monetary_amount(row[3])
    kind = row[1]
    description = row[2]
    closing_balance = _parse_monetary_amount(row[4])
    return Transaction(date, amount, kind, description, closing_balance)

Midata = StatementReader(_MIDATA_HEADER, _midata_parse_transaction)

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

    return date(year, month, day)

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

Nationwide = StatementReader(_NATIONWIDE_HEADER, _nationwide_parse_transaction)

# use this
logger = logging.getLogger("natpar")

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
            logger.warning(f'Could not detect a statement format for "{file_basename}"')
            return None
        for fmt in statement_formats:
            if line.strip() == fmt.header:
                statement_format = fmt
                logger.debug(f'Format for "{file_basename}" detected as {statement_format}')
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
