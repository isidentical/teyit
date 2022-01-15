import unittest


class TestCase(unittest.TestCase):

    def test_random(self):
        self.assertIsNone(
            x, # ensure that x is None
            msg='x is None'
        )
        self.assertIsInstance(
            y,
            bool,
            'y is a bool' # y is a bool
        )
        self.assertIsInstance(
            y, # y is a bool
            bool,
            some_args_that_shouldnt,
            exist_but_we_still_care,
            'y is a bool' # y is a bool
        )
        self.assertIsInstance(
            y,
            bool,
            some_args_that_shouldnt, # test is a bool
            exist_but_we_still_care, # y is a bool
            'y is a bool'
        )
        self.assertIsNone(
            x, # this is X
            msg="test" # this is the message
        )
