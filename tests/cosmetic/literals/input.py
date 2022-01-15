import unittest


class TestCase(unittest.TestCase):

    def test_random(self):
        self.assertIs(
            1e400,
            True,
            msg="""
            complex
            string"""
        )
        self.assertIs(
            2                     + 2,
            False
        )
