import unittest


class TestCase(unittest.TestCase):

    def test_random(self):
        self.assertTrue(
            1e400,
            msg="""
            complex
            string"""
        )
        self.assertFalse(
            2                     + 2
        )
