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

    # TODO: could this be converted to "redate if ordering not valid"?
    def date_ordering_is_valid(self, previous_transaction, new_transaction):
        if self._transaction_ordering == self.TransactionOrder.CHRONOLOGICAL:
            return new_transaction.date >= previous_transaction.date
        else:
            return new_transaction.date <= previous_transaction.date

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

def append_transaction(statement_format, transaction_list, new_transaction):
    """Append a transaction to a nonempty list of transactions, accounting for edge cases with interest payments.

    TODO: redesign so statement_format parameter is unnecessary."""

    # happy path - the transaction follows nicely
    if statement_format.validate(transaction_list[-1], new_transaction):
        transaction_list.append(new_transaction)
        return True

    # if the new transaction is interest, try redating it
    if new_transaction.is_interest():
        redated_new_transaction = new_transaction.redate(transaction_list[-1].date)
        if statement_format.validate(transaction_list[-1], redated_new_transaction):
            transaction_list.append(redated_new_transaction)
            logger.debug(f"Appended transaction {redated_new_transaction} after redating it from {new_transaction.date} to {redated_new_transaction.date}")
            return True

    # if the last existing transaction is interest, try redating it
    if transaction_list[-1].is_interest():
        redated_existing_transaction = transaction_list[-1].redate(new_transaction.date)
        # always check -1 -> new
        # check -2 -> -1 if len > 1
        if statement_format.validate(redated_existing_transaction, new_transaction) and (len(transaction_list) <= 1 or statement_format.validate(transaction_list[-2], redated_existing_transaction)):
            original_interest_date = transaction_list[-1].date
            transaction_list[-1] = redated_existing_transaction
            transaction_list.append(new_transaction)
            logger.debug(f"Appended transaction {new_transaction} after redating prior interest transaction from {original_interest_date} to {redated_existing_transaction.date}")
            return True

    # out of ideas
    return False

def insert_interest_transaction(statement_format, transaction_list, new_transaction, target_index):
    """Insert an interest transaction into a nonempty list of transactions, accounting for edge cases with interest payments.

    TODO: redesign so statement_format parameter is unnecessary."""

    # validation
    if target_index == 0 or target_index > len(transaction_list):
        logger.warn(f"Attempted to insert a transaction at invalid index {target_index} - transaction_list length is {len(transaction_list)}")
        return False

    # delegate to append if applicable
    if target_index == len(transaction_list):
        return append_transaction(statement_format, transaction_list, new_transaction)

    # redate interest transaction if the date is wrong
    maybe_transaction = new_transaction.copy()
    if not (statement_format.date_ordering_is_valid(transaction_list[target_index - 1], maybe_transaction) and statement_format.date_ordering_is_valid(maybe_transaction, transaction_list[target_index])):
        maybe_transaction = maybe_transaction.redate(min(transaction_list[target_index - 1].date, transaction_list[target_index].date))
        logger.debug(f"Redating transaction to {maybe_transaction.date} before attempting insertion")

    if statement_format.validate(transaction_list[target_index - 1], maybe_transaction) and statement_format.validate(maybe_transaction, transaction_list[target_index]):
        transaction_list.insert(target_index, maybe_transaction)
        logger.debug(f"Successfully inserted transaction {maybe_transaction}")
        return True

    # out of ideas
    return False

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

    discontinuous_transaction_index = None     # "gap" into which an interest payment can be moved
    misplaced_interest_transaction = None      # interest payment which needs reordering

    for row in c:
        if len(row) == 0:
            # reached end of transactions
            break

        try:
            new_transaction = statement_format.parse_transaction(row)
            logger.debug(f"Parsed transaction: {new_transaction}")

            # first transaction
            if len(transactions) == 0:
                transactions.append(new_transaction)
                continue

            # append, potentially with known adjustments
            previous_transaction = transactions[-1]
            if append_transaction(statement_format, transactions, new_transaction):
                continue

            # out of order transaction
            #
            # rather than building arbitrarily complex transaction reordering logic, just cover known cases.
            #
            # assumptions:
            # - the first transaction (chronologically and by statement order) in a statement is consistent
            # - the statement can be made consistent by reordering and/or redating interest payments
            # - multiple interest payments that need rearranging will not overlap or affect each other in any way (likely only one per month)
            #
            # handle an interest transaction
            if new_transaction.is_interest():
                logger.debug("Found an out of order interest transaction")

                # make sure no other interest transactions are being handled
                if misplaced_interest_transaction is not None:
                    raise StatementParseError("Encountered an out of order interest transaction while handling another")

                # try inserting if we've stored an index
                if discontinuous_transaction_index is not None:
                    if insert_interest_transaction(statement_format, transactions, new_transaction, discontinuous_transaction_index):
                        discontinuous_transaction_index = None
                        logger.debug("Successfully inserted out of order interest transaction in stored index")
                        continue
                    else:
                        raise StatementParseError("Out of order interest transaction could not be inserted into expected gap")

                # store for later to see if it can be moved
                misplaced_interest_transaction = new_transaction
                logger.debug("Saved an interest transaction to be looked at later")

            # handle a non-interest transaction
            else:
                logger.debug("Found an inconsistent transaction")

                # make sure no other inconsistent transactions are being handled
                if discontinuous_transaction_index is not None:
                    raise StatementParseError("Encountered an inconsistent non-interest transaction while handling another")

                # try inserting a stored interest transaction if available
                if misplaced_interest_transaction is not None:
                    # TODO: can this block be factored into append_transaction or some other function?
                    #
                    # redate interest transaction if the date is wrong
                    test_transaction = misplaced_interest_transaction.copy()
                    if not statement_format.date_ordering_is_valid(previous_transaction, test_transaction):
                        test_transaction = test_transaction.redate(min(previous_transaction.date, new_transaction.date))

                    if statement_format.validate(previous_transaction, test_transaction) and statement_format.validate(test_transaction, new_transaction):
                        transactions.append(test_transaction)
                        transactions.append(new_transaction)
                        misplaced_interest_transaction = None
                        logger.debug("Successfully inserted stored interest transaction with new transaction")
                        continue
                    else:
                        raise StatementParseError("Inconsistent interest transaction could not be inserted into other transactions")

                # insert anyway and mark for later to see if an interest transaction can be inserted here
                discontinuous_transaction_index = len(transactions)
                transactions.append(new_transaction)
                logger.debug("Saved an index for an upcoming out of order interest transaction")

        except Exception as e:
            f.close()
            raise StatementParseError(e)

    f.close()
    logger.debug(f'Reached end of file "{file_basename}"')

    # make sure any inconsistent transactions were handled
    if discontinuous_transaction_index is not None:
        raise StatementParseError(f"Could not reconcile inconsistent transaction: {transactions[discontinuous_transaction_index]}")
    if misplaced_interest_transaction is not None and not append_transaction(statement_format, transactions, misplaced_interest_transaction):
        raise StatementParseError(f"Could not reconcile inconsistent interest transaction: {misplaced_interest_transaction}")

    return (account_name, statement_format.order(transactions))
