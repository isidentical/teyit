import argparse
import ast
import copy
import tokenize
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from refactor.ast import PreciseUnparser

OPERATOR_TABLE = {
    ast.Eq: "assertEqual",
    ast.NotEq: "assertNotEqual",
    ast.Lt: "assertLess",
    ast.LtE: "assertLessEqual",
    ast.Gt: "assertGreater",
    ast.GtE: "assertGreaterEqual",
    ast.In: "assertIn",
    ast.NotIn: "assertNotIn",
    ast.Is: "assertIs",
    ast.IsNot: "assertIsNot",
}

CONTRA_OPS = {ast.Eq: ast.NotEq, ast.In: ast.NotIn, ast.Is: ast.IsNot}

for key, value in CONTRA_OPS.copy().items():
    CONTRA_OPS[value] = key

DEPRECATED_ALIASES = {
    "assert_": "assertTrue",
    "failIf": "assertFalse",
    "failUnless": "assertTrue",
    "assertEquals": "assertEqual",
    "failIfEqual": "assertNotEqual",
    "failUnlessEqual": "assertEqual",
    "assertNotEquals": "assertNotEqual",
    "assertAlmostEquals": "assertAlmostEqual",
    "failIfAlmostEqual": "assertNotAlmostEqual",
    "failUnlessAlmostEqual": "assertAlmostEqual",
    "assertNotAlmostEquals": "assertNotAlmostEqual",
    "assertRegexpMatches": "assertRegex",
    "assertNotRegexpMatches": "assertNotRegex",
}


@dataclass
class Rewrite:
    node: ast.Call
    func: str
    args: List[ast.AST]

    def __hash__(self):
        return hash(id(self))

    @lru_cache(maxsize=1)
    def build_node(self):
        new_node = copy.deepcopy(self.node)
        new_node.func.attr = self.func
        new_node.args = self.args
        return new_node

    @lru_cache(maxsize=1)
    def get_arg_offset(self):
        new_node = self.build_node()
        prev_args = len(self.node.args + self.node.keywords)
        return len(new_node.args + new_node.keywords) - prev_args


class _AssertRewriter(ast.NodeVisitor):
    def __init__(self, blacklist=frozenset(), *args, **kwargs):
        self.asserts = []
        self.blacklist = blacklist
        super().__init__(*args, **kwargs)

    def visit_Call(self, node):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and ast.unparse(node.func.value) == "self"
            and node.func.attr not in self.blacklist
        ):
            return node
        visitor_proc = f"visit_{node.func.attr}"
        with suppress(Exception):
            if node.func.attr in DEPRECATED_ALIASES:
                self.asserts.append(
                    Rewrite(
                        node, DEPRECATED_ALIASES[node.func.attr], node.args
                    )
                )
            elif not hasattr(self, visitor_proc):
                return node
            elif rewrite := getattr(self, visitor_proc)(node):
                self.asserts.append(rewrite)

    def visit_assertTrue(self, node, positive=True):
        expr, *args = node.args
        if isinstance(expr, ast.Compare) and len(expr.ops) == 1:
            left = expr.left
            operator = type(expr.ops[0])
            if not positive:
                if operator in CONTRA_OPS:
                    operator = CONTRA_OPS[operator]
                else:
                    return None

            (comparator,) = expr.comparators
            if (
                operator in (ast.Is, ast.IsNot)
                and isinstance(comparator, ast.Constant)
                and comparator.value is None
            ):

                func = f"assert{operator.__name__}None"
                args = [left, *args]
            elif operator in OPERATOR_TABLE:
                func = OPERATOR_TABLE[operator]
                args = [left, comparator, *args]
            else:
                return None
        elif (
            isinstance(expr, ast.Call)
            and ast.unparse(expr.func) == "isinstance"
            and len(expr.args) == 2
        ):
            if positive:
                func = "assertIsInstance"
            else:
                func = "assertNotIsInstance"
            args = [*expr.args, *args]
        else:
            return None
        return Rewrite(node, func, args)

    def visit_assertFalse(self, node):
        return self.visit_assertTrue(node, positive=False)

    def visit_assertIs(self, node, positive=True):
        left, right, *args = node.args
        if isinstance(right, ast.Constant):
            if (
                right.value in (True, False)
                and isinstance(right.value, bool)
                and positive
            ):
                func = f"assert{right.value}"
            elif right.value is None:
                if positive:
                    func = "assertIsNone"
                else:
                    func = "assertIsNotNone"
            args = [left, *args]
        else:
            return None
        return Rewrite(node, func, args)

    def visit_assertIsNot(self, node):
        return self.visit_assertIs(node, positive=False)

    def visit_assertDictContainsSubset(self, node):
        left, right, *args = node.args
        func = "assertEqual"
        args = [
            right,
            ast.Dict(keys=[None, None], values=[right, left]),
            *args,
        ]
        return Rewrite(node, func, args)


class _FormattedUnparser(PreciseUnparser):
    def __init__(self, indent_width=4, comments=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_first_call = True
        self._indent_text = " " * indent_width
        self._comments = comments

    def visit_Call(self, node):
        first_call = self._is_first_call
        if self._is_first_call:
            self._is_first_call = False
        self.set_precedence(ast._Precedence.ATOM, node.func)
        self.traverse(node.func)
        self.write("(")
        self._indent += 1

        total_args = len(node.args + node.keywords)
        for n, item in enumerate(node.args + node.keywords):
            add_comma = n + 1 != total_args
            if first_call:
                self.fill()
            self.traverse(item)

            if add_comma:
                self.write(",")
            if first_call:
                if comment := self._comments.get(n):
                    self.write(f" {comment}")
            elif add_comma:
                self.write(" ")
        self._indent -= 1
        if first_call:
            self.fill()
        self.write(")")


def as_source(
    source, node, *, is_multi_line=False, comments=None, next_indent=4
):
    indent = node.col_offset
    if is_multi_line:
        formatted_unparser = _FormattedUnparser(
            source=source, indent_width=next_indent, comments=comments
        )
        formatted_unparser._indent = node.col_offset // next_indent
        source = formatted_unparser.unparse(node)
    else:
        regular_unparser = PreciseUnparser(source=source)
        source = regular_unparser.unparse(node)

    source = " " * indent + source
    if comments is not None and len(comments) >= 1 and not is_multi_line:
        source += " " + comments.popitem()[1]
    return source


def recover_comments(source_lines):
    comments, arg_lines = {}, set()
    with suppress(tokenize.TokenError):
        nesting = -1
        tokens = tuple(tokenize.generate_tokens(iter(source_lines).__next__))
        for index, token in enumerate(tokens):
            if token.string in "([{":
                nesting += 1
            elif token.string in ")]}":
                nesting -= 1

            if nesting == 0 and token.exact_type == tokenize.COMMA:
                arg_lines.add(token.start[0])
            elif nesting == -1 and token.exact_type == tokenize.RPAR:
                arg_lines.add(tokens[index - 1].start[0])

            if token.type == tokenize.COMMENT:
                comments[token.start[0]] = token.string

        return {
            arg_index: comments[arg_line]
            for arg_index, arg_line in enumerate(arg_lines)
            if arg_line in comments
        }


def _adjust_comments(comments, arg_offset):
    for operation, arg_index in enumerate(reversed(comments.copy().keys())):
        if operation > arg_index:
            break
        comment = comments.pop(arg_index)
        comments[arg_index + arg_offset] = comment
    return comments


def rewrite_source(source, *, blacklist=frozenset()):
    if len(source) == 0:
        return source, []

    original_source = source
    tree = ast.parse(source)
    rewriter = _AssertRewriter(blacklist=blacklist)
    rewriter.visit(tree)

    offset_shift = 0
    trailing_newline = source[-1] == "\n"
    for rewrite in rewriter.asserts:
        node = rewrite.node
        lines = source.splitlines()  # todo: ast._splitlines_no_ff
        start, end = (
            node.lineno - 1 - offset_shift,
            node.end_lineno - offset_shift,
        )
        comments = recover_comments(lines[start:end])
        new_source = as_source(
            original_source,
            rewrite.build_node(),
            is_multi_line=end - 1 - start,
            comments=_adjust_comments(comments, rewrite.get_arg_offset()),
        )
        lines[start:end] = (new_source,)
        source = "\n".join(lines)
        if trailing_newline:
            source += "\n"
        offset_shift += end - len(new_source.splitlines()) - start
    return source, rewriter.asserts


def refactor_until_deterministic(source, blacklist=frozenset(), *, max=5):
    refactors = []
    for iteration in range(max):
        source, _refactors = rewrite_source(source, blacklist=blacklist)
        if len(_refactors) == 0:
            break
        refactors.extend(_refactors)
    return source, refactors


def refactor(self, source, **kwargs):
    source, _ = refactor_until_deterministic(source, **kwargs)
    return source


def _glob_files(paths, pattern):
    for path in paths:
        if path.is_dir():
            yield from path.glob(pattern)
        elif path.is_file():
            yield path


def _show_debug_stats(modified_files, refactors):
    results = defaultdict(int)
    for refactor in refactors:
        results[refactor.node.func.attr, refactor.func] += 1
    for key, amount in sorted(results.items(), key=lambda kv: kv[1]):
        print(
            "{:25}=> {:25}".format(*key),
            "refactoring happened",
            amount,
            "times.",
        )
    print(
        f"{len(refactors)} assertions (in {modified_files} files) have been"
        " refactored."
    )


def _refactor_file(path, **kwargs):
    with tokenize.open(path) as file:
        source = file.read()
        encoding = file.encoding
    refactored_source, refactors = refactor_until_deterministic(
        source, **kwargs
    )
    if refactored_source != source:
        path.write_text(refactored_source, encoding=encoding)
    return refactors


def _refactor_files(paths, pattern, show_stats=False, fail_on_change=False):
    modified_files, total_refactors = 0, []
    files = tuple(_glob_files(paths, pattern=pattern))
    for path in files:
        if len(refactors := _refactor_file(path)) > 0:
            modified_files += 1
            total_refactors.extend(refactors)
            print(f"reformatted {path}")

    if len(files) > 0:
        message = ["All done!"]
        if modified_files > 0:
            message.append(f" {modified_files} reformatted")
        if (left := len(files) - modified_files) > 0:
            if len(message) > 1:
                message.append(",")
            message.append(f" {left} left unchanged")
        print("".join(message))
        if fail_on_change and modified_files > 0:
            return 1
    else:
        print("Nothing to refactor!")

    if show_stats:
        _show_debug_stats(modified_files, total_refactors)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="*")
    parser.add_argument(
        "--pattern",
        default="test_*.py",
        help="Wildcard pattern for capturing test files.",
    )
    parser.add_argument(
        "--show-stats",
        action="store_true",
        help="Print out some debug stats related about refactorings",
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        help="Exit with status code 1 if any file changed",
    )
    options = parser.parse_args()
    raise SystemExit(_refactor_files(**vars(options)))


if __name__ == "__main__":
    main()
