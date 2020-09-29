import ast
import unittest
from pathlib import Path
from textwrap import dedent

import teyit

TEST_DATA_DIR = Path(__file__).parent


class TeyitTestCase(unittest.TestCase):
    def assertRewrites(self, given, expected, case_count=None, **kwargs):
        with self.subTest(given=given, expected=expected, **kwargs):
            source, cases = teyit.refactor_until_deterministic(given)
            self.assertEqual(source, expected)
            if case_count is not None:
                self.assertEqual(len(cases), case_count)

    def assertNotRewrites(self, given):
        self.assertRewrites(given, given, case_count=0)

    def test_rewrite(self):
        func = ast.parse("self.assertTrue(x is None)", mode="eval").body
        rewrite = teyit.Rewrite(func, "assertIsNone", [func.args[0].left])
        self.assertEqual(
            ast.unparse(rewrite.build_node()), "self.assertIsNone(x)"
        )
        self.assertEqual(rewrite.get_arg_offset(), 0)

        func = ast.parse("self.assertTrue(a == b)", mode="eval").body
        rewrite = teyit.Rewrite(
            func, "assertEqual", [func.args[0].left, *func.args[0].comparators]
        )
        self.assertEqual(rewrite.get_arg_offset(), 1)

        func = ast.parse(
            "self.assertTrue(x is None, message='XYZ')", mode="eval"
        ).body
        rewrite = teyit.Rewrite(func, "assertIsNone", [func.args[0].left])
        self.assertEqual(
            ast.unparse(rewrite.build_node()),
            "self.assertIsNone(x, message='XYZ')",
        )

        func = ast.parse(
            "self.assertIs(x, None, message='XYZ')", mode="eval"
        ).body
        rewrite = teyit.Rewrite(func, "assertIsNone", [func.args[0]])
        self.assertEqual(rewrite.get_arg_offset(), -1)

    def test_assert_rewriter_basic(self):
        self.assertRewrites(
            "self.assertTrue(x == y)", "self.assertEqual(x, y)"
        )
        self.assertRewrites(
            "self.assertTrue(x != y)", "self.assertNotEqual(x, y)"
        )
        self.assertRewrites("self.assertTrue(x < y)", "self.assertLess(x, y)")
        self.assertRewrites(
            "self.assertTrue(x <= y)", "self.assertLessEqual(x, y)"
        )
        self.assertRewrites(
            "self.assertTrue(x > y)", "self.assertGreater(x, y)"
        )
        self.assertRewrites(
            "self.assertTrue(x >= y)", "self.assertGreaterEqual(x, y)"
        )
        self.assertRewrites("self.assertTrue(x in y)", "self.assertIn(x, y)")
        self.assertRewrites(
            "self.assertTrue(x not in y)", "self.assertNotIn(x, y)"
        )
        self.assertRewrites("self.assertTrue(x is y)", "self.assertIs(x, y)")
        self.assertRewrites(
            "self.assertTrue(x is not y)", "self.assertIsNot(x, y)"
        )
        self.assertRewrites(
            "self.assertTrue(x is None)", "self.assertIsNone(x)"
        )
        self.assertRewrites(
            "self.assertTrue(x is not None)", "self.assertIsNotNone(x)"
        )
        self.assertRewrites(
            "self.assertTrue(isinstance(x, y))", "self.assertIsInstance(x, y)"
        )
        self.assertRewrites(
            "self.assertTrue(isinstance(x, (y, z)))",
            "self.assertIsInstance(x, (y, z))",
        )

        self.assertRewrites(
            "self.assertFalse(x == y)", "self.assertNotEqual(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x != y)", "self.assertEqual(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x in y)", "self.assertNotIn(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x not in y)", "self.assertIn(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x is y)", "self.assertIsNot(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x is not y)", "self.assertIs(x, y)"
        )
        self.assertRewrites(
            "self.assertFalse(x is None)", "self.assertIsNotNone(x)"
        )
        self.assertRewrites(
            "self.assertFalse(x is not None)", "self.assertIsNone(x)"
        )
        self.assertRewrites(
            "self.assertFalse(isinstance(x, y))",
            "self.assertNotIsInstance(x, y)",
        )
        self.assertRewrites(
            "self.assertFalse(isinstance(x, (y, z)))",
            "self.assertNotIsInstance(x, (y, z))",
        )

        self.assertRewrites("self.assertIs(x, True)", "self.assertTrue(x)")
        self.assertRewrites("self.assertIs(x, False)", "self.assertFalse(x)")
        self.assertRewrites("self.assertIs(x, None)", "self.assertIsNone(x)")

        self.assertNotRewrites("self.assertIsNot(x, True)")
        self.assertNotRewrites("self.assertIsNot(x, False)")
        self.assertRewrites(
            "self.assertIsNot(x, None)", "self.assertIsNotNone(x)"
        )

    def test_assert_rewriter_multiple(self):
        self.assertRewrites(
            "self.assertIs(x is y, True)", "self.assertIs(x, y)"
        )
        self.assertRewrites(
            "self.assertIs(x is y, False)", "self.assertIsNot(x, y)"
        )
        self.assertRewrites(
            "self.assertIs(isinstance(x, T), False)",
            "self.assertNotIsInstance(x, T)",
        )

    def test_assert_rewriter_deprecated(self):
        # Regenerate tests
        # template = "self.{key}(x, y, z, msg=msg)"
        # print(
        #     "\n".join(
        #         [
        #             f"self.assertRewrites({template.format(key=key)!r}, {template.format(key=value)!r})"
        #             for key, value in DEPRECATED_ALIASES.items()
        #         ]
        #     )
        # )

        self.assertRewrites(
            "self.assert_(x, y, z, msg=msg)",
            "self.assertTrue(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failIf(x, y, z, msg=msg)",
            "self.assertFalse(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failUnless(x, y, z, msg=msg)",
            "self.assertTrue(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.assertEquals(x, y, z, msg=msg)",
            "self.assertEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failIfEqual(x, y, z, msg=msg)",
            "self.assertNotEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failUnlessEqual(x, y, z, msg=msg)",
            "self.assertEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.assertNotEquals(x, y, z, msg=msg)",
            "self.assertNotEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.assertAlmostEquals(x, y, z, msg=msg)",
            "self.assertAlmostEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failIfAlmostEqual(x, y, z, msg=msg)",
            "self.assertNotAlmostEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.failUnlessAlmostEqual(x, y, z, msg=msg)",
            "self.assertAlmostEqual(x, y, z, msg=msg)",
        )
        self.assertRewrites(
            "self.assertNotAlmostEquals(x, y, z, msg=msg)",
            "self.assertNotAlmostEqual(x, y, z, msg=msg)",
        )

    def test_assert_rewriter_cosmetic(self):
        for case in (TEST_DATA_DIR / "cosmetic").iterdir():
            self.assertRewrites(
                (case / "input.py").read_text(),
                (case / "output.py").read_text(),
                case=case,
            )


if __name__ == "__main__":
    unittest.main()
