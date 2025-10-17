import os
import unittest

from statements import read_nationwide_file
from transaction import Transaction


TEST_DATA_DIR = "fixtures"

class TestFileParsing(unittest.TestCase):
    def test_parse_random_file(self):
        infile = os.path.join(TEST_DATA_DIR, "random-file.txt")
        result = read_nationwide_file(infile)

        self.assertIsNone(result)

    def test_parse_midata(self):
        infile = os.path.join(TEST_DATA_DIR, "test-midata.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 8)

    def test_parse_statement(self):
        infile = os.path.join(TEST_DATA_DIR, "test-statement.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 6)

class TestFileTransactions(unittest.TestCase):
    def test_statement_consistency(self):
        infile = os.path.join(TEST_DATA_DIR, "test-statement.csv")
        result = read_nationwide_file(infile)

        last_transaction = None
        for transaction in result:
            if last_transaction is None:
                last_transaction = transaction
                continue

            self.assertEqual(last_transaction.closing_balance + transaction.amount, transaction.closing_balance)
            self.assertGreaterEqual(transaction.date, last_transaction.date)
            last_transaction = transaction

    def test_midata_consistency(self):
        infile = os.path.join(TEST_DATA_DIR, "test-midata.csv")
        result = read_nationwide_file(infile)

        last_transaction = None
        for transaction in result:
            if last_transaction is None:
                last_transaction = transaction
                continue

            self.assertEqual(last_transaction.closing_balance + transaction.amount, transaction.closing_balance)
            self.assertGreaterEqual(transaction.date, last_transaction.date)
            last_transaction = transaction

if __name__ == "__main__":
    unittest.main()
