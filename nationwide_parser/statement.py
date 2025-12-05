import csv
import datetime
import enum
import logging
import os
import re

from nationwide_parser.transaction import Transaction


logger = logging.getLogger(__name__)

class StatementReader():
    class TransactionOrder(enum.Enum):
        CHRONOLOGICAL = 1
        REVERSE_CHRONOLOGICAL = -1

    def __init__(self, name, header, account_regex, parse_raw_transaction, transaction_ordering):
        self.name = name
        self.header = header
        self._transaction_fields = header.count(",") + 1
        self._account_regex = re.compile(account_regex)
        self._parse_raw_transaction = parse_raw_transaction

        if not isinstance(transaction_ordering, self.TransactionOrder):
            raise ValueError("transaction_ordering must be a member of StatementReader.TransactionOrder")
        self._transaction_ordering = transaction_ordering

    def __str__(self):
        return self.name

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
        if self._transaction_ordering == self.TransactionOrder.CHRONOLOGICAL:
            return results
        else:
            return results[::-1]

    def validate(self, previous_transaction, new_transaction):
        if self._transaction_ordering == self.TransactionOrder.CHRONOLOGICAL:
            return new_transaction.succeeds(previous_transaction)
        else:
            return previous_transaction.succeeds(new_transaction)

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

Midata = StatementReader("Midata", _MIDATA_HEADER, r'"Account Number:","([^"]+)"', _midata_parse_transaction, StatementReader.TransactionOrder.REVERSE_CHRONOLOGICAL)


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

Nationwide = StatementReader("Nationwide statement", _NATIONWIDE_HEADER, r'"Account Name:","[^"*]*(\*+\d+)"', _nationwide_parse_transaction, StatementReader.TransactionOrder.CHRONOLOGICAL)

class StatementParseError(Exception):
    """Raised when a file can't be parsed into a name and list of
    transactions"""

    pass

def read_nationwide_file(file):
    file_basename = os.path.basename(file)
    logger.debug(f'Reading file "{file_basename}"')

    # Nationwide exports files encoded with ISO-8859-1, using CRLF terminators
    f = open(file, encoding="latin_1")

    # check file not empty
    line = f.readline()
    if line == '': # EOF
        f.close()
        raise StatementParseError(f'"{file_basename}" is empty')

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
        f.close()
        raise StatementParseError(f'Could not detect a statement format for "{file_basename}"')

    # skip through lines until we hit the CSV header
    while (True):
        line = f.readline()
        if line == '': # EOF
            f.close()
            raise StatementParseError(f'Could not detect start of transaction data for "{file_basename}"')
        elif line.strip() == statement_format.header:
            logger.debug(f'Detected start of transaction data for "{file_basename}"')
            break

    # parse rest of file as CSV
    c = csv.reader(f)

    transactions = []
    for row in c:
        # only applicable to midata
        if len(row) == 0:
            break
        try:
            old_transaction = transactions[-1] if len(transactions) > 0 else None
            new_transaction = statement_format.parse_transaction(row)
            logger.debug(f"Parsed transaction: {new_transaction}")

            if old_transaction is not None and not statement_format.validate(old_transaction, new_transaction):
                raise StatementParseError(f"Statement contains inconsistent transaction order: {old_transaction} -> {new_transaction}")

            transactions.append(new_transaction)

        except Exception as e:
            f.close()
            raise StatementParseError(e)

    logger.debug(f'Reached end of file "{file_basename}"')
    f.close()
    return (account_name, statement_format.order(transactions))
