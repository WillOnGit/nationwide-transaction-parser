import os
import unittest

from statements import read_nationwide_file


TEST_DATA_DIR = "fixtures"

class TestInputData(unittest.TestCase):
    def test_parse_random_file(self):
        infile = os.path.join(TEST_DATA_DIR, "random-file.txt")
        result = read_nationwide_file(infile)

        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
