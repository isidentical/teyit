import unittest


class TestCase(unittest.TestCase):

    def test_random(self):
        self.assertIsNone(x, msg='x is None') # ensure that x is None
        self.assertIsInstance(y, bool, 'y is a bool') # y is a bool
