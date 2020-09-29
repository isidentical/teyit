# Teyit
A static analyzer and a refactoring tool to rewrite your unittest assertions in the right way.

## Usage
```
usage: teyit [-h] [--pattern PATTERN] [--show-stats] [--fail-on-change] [paths ...]

positional arguments:
  paths

optional arguments:
  -h, --help         show this help message and exit
  --pattern PATTERN  Wildcard pattern for capturing test files.
  --show-stats       Print out some debug stats related about refactorings
  --fail-on-change   Exit with status code 1 if any file changed
```
### Pre-commit Hook
```
-   repo: https://github.com/isidentical/teyit
    rev: master
    hooks:
    -   id: teyit
```

### Public API
- `teyit.refactor(source: str, **kwargs) -> str`, Shortcut to `refactor_until_deterministic`, for only retrieving the source code.
- `def refactor_until_deterministic(source: str, blacklist: FrozenSet[str] = frozenset(), *, max: int = 5) -> Tuple[str, List[Rewrite]]`, Run `rewrite_source` until it can't refactor no more (or the `max` limit reached).
- `def rewrite_source(source: str, *, blacklist: FrozenSet[str] = frozenset()): -> Tuple[str, List[Rewrite]]`, Refactor the source code changing assertion cases to the right forms. The `blacklist` parameter is a frozenset of functions that shouldn't refactored (e.g: `frozenset(('assertX', 'assertY'))`).

## Examples
These are some examples inside of the CPython itself. It is the primary
test target for teyit (since it is the biggest codebase that uses unittest
AFAIK). On the CI we build the master branch of it with refactoring the test suite with
teyit (it found over 1000 cases) and run the tests to see if any behavior changed.
```diff
>>> b/Lib/test/test_telnetlib.py
-        self.assertTrue(len(cmd) > 0) # we expect at least one command
+        self.assertGreater(len(cmd), 0) # we expect at least one command
>>> b/Lib/test/test___future__.py
@@ -13,9 +13,10 @@ class FutureTest(unittest.TestCase):
         for name in dir(__future__):
             obj = getattr(__future__, name, None)
             if obj is not None and isinstance(obj, __future__._Feature):
-                self.assertTrue(
-                    name in given_feature_names,
-                    "%r should have been in all_feature_names" % name
+                self.assertIn(
+                    name,
+                    given_feature_names,
+                    '%r should have been in all_feature_names' % name
                 )
>>> b/Lib/test/test_abc.py
@@ -321,14 +321,14 @@ def test_factory(abc_ABCMeta, abc_get_cache_token):
             class B:
                 pass
             b = B()
-            self.assertFalse(isinstance(b, A))
+            self.assertNotIsInstance(b, A)
             token_old = abc_get_cache_token()
             A.register(B)
             token_new = abc_get_cache_token()
             self.assertGreater(token_new, token_old)
-            self.assertTrue(isinstance(b, A))
+            self.assertIsInstance(b, A)
>>> b/Lib/test/test_array.py
@@ -456,39 +456,39 @@ class BaseTest:
 
     def test_cmp(self):
         a = array.array(self.typecode, self.example)
-        self.assertIs(a == 42, False)
-        self.assertIs(a != 42, True)
+        self.assertNotEqual(a, 42)
+        self.assertNotEqual(a, 42)
>>> b/Lib/test/test_asyncore.py
@@ -306,7 +306,7 @@ class DispatcherTests(unittest.TestCase):
         if hasattr(os, 'strerror'):
             self.assertEqual(err, os.strerror(errno.EPERM))
         err = asyncore._strerror(-1)
-        self.assertTrue(err != "")
+        self.assertNotEqual(err, '')
>>> b/Lib/test/test_bigmem.py
-        self.assertTrue(SUBSTR in s)
-        self.assertFalse(SUBSTR * 2 in s)
-        self.assertTrue(_('-') in s)
-        self.assertFalse(_('a') in s)
+        self.assertIn(SUBSTR, s)
+        self.assertNotIn(SUBSTR * 2, s)
+        self.assertIn(_('-'), s)
+        self.assertNotIn(_('a'), s)
>>> b/Lib/test/test_builtin.py
@@ -175,7 +175,7 @@ class BuiltinTest(unittest.TestCase):
         self.assertEqual(abs(0), 0)
         self.assertEqual(abs(1234), 1234)
         self.assertEqual(abs(-1234), 1234)
-        self.assertTrue(abs(-sys.maxsize-1) > 0)
+        self.assertGreater(abs(-sys.maxsize - 1), 0)
```
