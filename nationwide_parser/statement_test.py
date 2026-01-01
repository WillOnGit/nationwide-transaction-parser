import os
import unittest

from nationwide_parser.account import Account
from nationwide_parser.statement import read_nationwide_file, StatementParseError


TEST_DATA_DIR = "fixtures"

class TestFileParsing(unittest.TestCase):
    def test_parse_random_file(self):
        infile = os.path.join(TEST_DATA_DIR, "random-file.txt")

        with self.assertRaises(StatementParseError):
            result = read_nationwide_file(infile)
            self.assertIsNone(result)

    def test_parse_midata(self):
        infile = os.path.join(TEST_DATA_DIR, "test-midata.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "****12345")
        self.assertIsInstance(result[1], list)

        self.assertEqual(len(result[1]), 8)

    def test_parse_midata_with_interest(self):
        infile = os.path.join(TEST_DATA_DIR, "midata-with-interest.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "****12345")
        self.assertIsInstance(result[1], list)

        self.assertEqual(len(result[1]), 10)

    def test_parse_bad_midatas(self):
        infiles = [f for f in os.listdir(TEST_DATA_DIR) if f.startswith('bad-midata') and f.endswith('.csv')]
        for file in infiles:
            with self.assertRaises(StatementParseError):
                result = read_nationwide_file(os.path.join(TEST_DATA_DIR, file))
                self.assertIsNone(result)

    def test_parse_statement(self):
        infile = os.path.join(TEST_DATA_DIR, "test-statement.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "****12345")
        self.assertIsInstance(result[1], list)

        self.assertEqual(len(result[1]), 6)

    def test_parse_statement_with_interest(self):
        infile = os.path.join(TEST_DATA_DIR, "statement-with-interest.csv")
        result = read_nationwide_file(infile)

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "****12345")
        self.assertIsInstance(result[1], list)

        self.assertEqual(len(result[1]), 8)

    def test_parse_bad_statements(self):
        infiles = [f for f in os.listdir(TEST_DATA_DIR) if f.startswith('bad-statement') and f.endswith('.csv')]
        for file in infiles:
            with self.assertRaises(StatementParseError):
                result = read_nationwide_file(os.path.join(TEST_DATA_DIR, file))
                self.assertIsNone(result)

class TestFileConsistency(unittest.TestCase):
    def test_statement_consistency(self):
        infile = os.path.join(TEST_DATA_DIR, "test-statement.csv")
        result = read_nationwide_file(infile)
        account = Account(result[0], result[1])

        self.assertTrue(account.all_transactions_are_continuous())

    def test_midata_consistency(self):
        infile = os.path.join(TEST_DATA_DIR, "test-midata.csv")
        result = read_nationwide_file(infile)
        account = Account(result[0], result[1])

        self.assertTrue(account.all_transactions_are_continuous())
