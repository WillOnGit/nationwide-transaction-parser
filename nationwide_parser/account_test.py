from datetime import date
import unittest

from nationwide_parser.transaction import Transaction
from nationwide_parser.account import Account, InconsistentTransactionsError


class TestTransactionMerging(unittest.TestCase):
    def setUp(self):
        self.test_account = Account("****11111", [
            Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
            Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
            Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
            Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
            ])

    def test_empty_merge(self):
        new_transactions = []
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 0)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
            ])

    def test_self_merge(self):
        num_added = self.test_account.add_unique_transactions(self.test_account.transactions)

        self.assertEqual(num_added, 0)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
            ])

    def test_equal_merge(self):
        new_transactions = [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                ]
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 0)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                ])

    def test_valid_earlier_merge(self):
        new_transactions = [
                Transaction(date(2025, 1, 1), 100, "abc", "xyz", 100), # new
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                ]
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 1)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 1, 1), 100, "abc", "xyz", 100),  # new
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                ])

    def test_valid_intermediate_merge(self):
        new_transactions = [
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 3), 100, "abc", "xyz", 1200), # new
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                ]
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 1)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 3), 100, "abc", "xyz", 1200), # new
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
            ])

    def test_valid_later_merge(self):
        new_transactions = [
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                Transaction(date(2025, 2, 5), -200, "abc", "xyz", 200), # new
                ]
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 1)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                Transaction(date(2025, 2, 5), -200, "abc", "xyz", 200), # new
            ])

    def test_valid_combined_merge(self):
        new_transactions = [
                Transaction(date(2025, 1, 1), 100, "abc", "xyz", 100), # new
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 3), 100, "abc", "xyz", 1200), # new
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                Transaction(date(2025, 2, 5), -200, "abc", "xyz", 200), # new
                ]
        num_added = self.test_account.add_unique_transactions(new_transactions)

        self.assertEqual(num_added, 3)
        self.assertEqual(self.test_account.transactions, [
                Transaction(date(2025, 1, 1), 100, "abc", "xyz", 100), # new
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 3), 100, "abc", "xyz", 1200), # new
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                Transaction(date(2025, 2, 5), -200, "abc", "xyz", 200), # new
            ])

    def test_invalid_first_merge(self):
        new_transactions = [
                Transaction(date(2025, 2, 1), 10, "abc", "xyz", 1000), # invalid
                Transaction(date(2025, 2, 1), 1, "abc", "xyz", 1001),
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                ]

        with self.assertRaises(InconsistentTransactionsError):
            self.test_account.add_unique_transactions(new_transactions)

    def test_invalid_second_merge(self):
        new_transactions = [
                Transaction(date(2025, 2, 2), 99, "abc", "xyz", 1100),
                Transaction(date(2025, 2, 4), -600, "abc", "xyz", 500),
                Transaction(date(2025, 2, 4), -300, "abc", "xyz", 200), # invalid
                Transaction(date(2025, 2, 4), -100, "abc", "xyz", 400),
                ]

        with self.assertRaises(InconsistentTransactionsError):
            self.test_account.add_unique_transactions(new_transactions)
