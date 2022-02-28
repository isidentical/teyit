import unittest


class NotACase:
    def not_a_case(self):
        assert 1 == 2


class WrongTestCase(unittest.TestCase):
    def not_a_case(self):
        assert isinstance(1, int)

    def test_without_self():
        assert 3 is 4  # comment


class CorrectTestCase(unittest.TestCase):
    def test_regular(self):
        assert self is not None  # comment
        assert isinstance(
            self,  # this is
            unittest.TestCase,  # multiline
        )
        assert 1 == 1  # eq

    assert True
assert True
