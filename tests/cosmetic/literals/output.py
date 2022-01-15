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

    def test_indented_long_string(self):
        self.assertIn(
            "Rejected:\n"
            "Launchpad failed to process the upload path '~name16/ubuntu':\n\n"
            "unicode PPA name: áří is disabled.\n\n"
            "It is likely that you have a configuration problem with "
            "dput/dupload.\n"
            "Please check the documentation at "
            "https://help.launchpad.net/Packaging/PPA/Uploading and update "
            "your configuration.\n\n"
            "Further error processing not possible because of a critical "
            "previous error.",
            body
        )
