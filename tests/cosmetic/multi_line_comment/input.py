import unittest


class TestCase(unittest.TestCase):

    def test_random(self):
        self.assertTrue(
            x is None, # ensure that x is None
            msg='x is None'
        )
        self.assertTrue(
            isinstance(y, bool),
            'y is a bool' # y is a bool
        )
        self.assertTrue(
            isinstance(y, bool), # y is a bool
            some_args_that_shouldnt,
            exist_but_we_still_care,
            'y is a bool' # y is a bool
        )
        self.assertTrue(
            isinstance(y, bool),
            some_args_that_shouldnt, # test is a bool
            exist_but_we_still_care, # y is a bool
            'y is a bool'
        )
        self.assertIs(
            x, # this is X
            None,
            msg="test" # this is the message
        )
