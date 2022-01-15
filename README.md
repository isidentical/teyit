# Teyit

An analyzer / formatter for your Python unit tests (more specifically, the tests written with the `unittest` module).

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

```yaml
-   repo: https://github.com/isidentical/teyit
    rev: master
    hooks:
    -   id: teyit
```

## Examples

Here are some examples from CPython's test suite:

```diff
--- a/Lib/test/test_telnetlib.py
+++ b/Lib/test/test_telnetlib.py
@@ -48,7 +48,7 @@ def testContextManager(self):
         self.assertIsNone(tn.get_socket())

     def testTimeoutDefault(self):
-        self.assertTrue(socket.getdefaulttimeout() is None)
+        self.assertIsNone(socket.getdefaulttimeout())
         socket.setdefaulttimeout(30)
         try:
             telnet = telnetlib.Telnet(HOST, self.port)
@@ -215,7 +215,7 @@ def test_read_some(self):
         # test 'at least one byte'
         telnet = test_telnet([b'x' * 500])
         data = telnet.read_some()
-        self.assertTrue(len(data) >= 1)
+        self.assertGreaterEqual(len(data), 1)
         # test EOF
         telnet = test_telnet()
         data = telnet.read_some()
```

```diff
--- a/Lib/test/test___future__.py
+++ b/Lib/test/test___future__.py
@@ -13,8 +13,9 @@ def test_names(self):
         for name in dir(__future__):
             obj = getattr(__future__, name, None)
             if obj is not None and isinstance(obj, __future__._Feature):
-                self.assertTrue(
-                    name in given_feature_names,
+                self.assertIn(
+                    name,
+                    given_feature_names,
                     "%r should have been in all_feature_names" % name
                 )
                 given_feature_names.remove(name)
```

```diff
--- a/Lib/test/test_abc.py
+++ b/Lib/test/test_abc.py
@@ -321,14 +321,14 @@ class A(metaclass=abc_ABCMeta):
             class B:
                 pass
             b = B()
-            self.assertFalse(isinstance(b, A))
-            self.assertFalse(isinstance(b, (A,)))
+            self.assertNotIsInstance(b, A)
+            self.assertNotIsInstance(b, (A,))
```

```diff
--- a/Lib/test/test_bigmem.py
+++ b/Lib/test/test_bigmem.py
@@ -536,25 +536,25 @@ def test_contains(self, size):
         edge = _('-') * (size // 2)
         s = _('').join([edge, SUBSTR, edge])
         del edge
-        self.assertTrue(SUBSTR in s)
-        self.assertFalse(SUBSTR * 2 in s)
-        self.assertTrue(_('-') in s)
-        self.assertFalse(_('a') in s)
+        self.assertIn(SUBSTR, s)
+        self.assertNotIn(SUBSTR * 2, s)
+        self.assertIn(_('-'), s)
+        self.assertNotIn(_('a'), s)
```

## Public API

#### `teyit.refactor(source: str, **kwargs) -> str`

Shortcut to `refactor_until_deterministic`, for only retrieving the source code.

#### `def refactor_until_deterministic(source: str, blacklist: FrozenSet[str] = frozenset(), *, max: int = 5) -> Tuple[str, List[Rewrite]]`

Run `rewrite_source` until it can't refactor no more (or the `max` limit reached).

#### `def rewrite_source(source: str, *, blacklist: FrozenSet[str] = frozenset()): -> Tuple[str, List[Rewrite]]`

Refactor the source code changing assertion cases to the right forms. The `blacklist` parameter is a frozenset of functions that shouldn't refactored (e.g: `frozenset(('assertX', 'assertY'))`).
