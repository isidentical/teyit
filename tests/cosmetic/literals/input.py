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

    def test_indented_long_string(self):
        self.assertTrue(
            "Rejected:\n"
            "Launchpad failed to process the upload path '~name16/ubuntu':\n\n"
            "unicode PPA name: áří is disabled.\n\n"
            "It is likely that you have a configuration problem with "
            "dput/dupload.\n"
            "Please check the documentation at "
            "https://help.launchpad.net/Packaging/PPA/Uploading and update "
            "your configuration.\n\n"
            "Further error processing not possible because of a critical "
            "previous error." in body
        )
