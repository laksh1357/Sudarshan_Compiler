"""
Test Suite for Differential Testing (differential_testing.py).

Tests cover:
  - Single level differential tests (O0–O3)
  - Full suite differential tests
  - Semantics preservation assertions
  - DiffTestCase and DiffTestSuite data structures
  - Edge cases: empty output, error propagation
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from differential_testing import (
    differential_test_level,
    differential_test,
    DiffTestCase,
    DiffTestSuite,
)


SIMPLE_PROGRAMS = [
    "print(42);",
    "int x = 10;\nprint(x);",
    "int a = 3 + 4;\nprint(a);",
    "int i = 0;\nwhile (i < 3) { i = i + 1; }\nprint(i);",
    "int x = 5;\nif (1) { x = 10; }\nprint(x);",
    "int a = 6;\nint b = a * 1;\nint c = b + 0;\nprint(c);",
]


class TestDiffTestLevel(unittest.TestCase):

    def test_returns_diff_test_case(self):
        case = differential_test_level("print(1);", level="O1")
        self.assertIsInstance(case, DiffTestCase)

    def test_simple_program_passes_all_levels(self):
        for level in ("O0", "O1", "O2", "O3"):
            case = differential_test_level("print(99);", level=level)
            self.assertTrue(case.passed,
                f"Level {level} failed: {case.failure_reason}\n{case.error}")

    def test_compile_error_produces_failed_case(self):
        case = differential_test_level("@@@invalid@@@", level="O1")
        self.assertFalse(case.passed)
        self.assertEqual(case.failure_reason, "compilation_error")

    def test_passed_case_has_matching_outputs(self):
        case = differential_test_level("int x = 7;\nprint(x);", level="O2")
        self.assertTrue(case.passed)
        self.assertEqual(case.reference_output, case.optimized_output)

    def test_raw_tac_text_populated_on_success(self):
        case = differential_test_level("print(5);", level="O1")
        self.assertIsInstance(case.raw_tac_text, str)
        self.assertTrue(len(case.raw_tac_text) > 0)

    def test_opt_report_populated_on_success(self):
        case = differential_test_level("int x = 5;\nint y = x + 0;\nprint(y);", level="O2")
        self.assertIsNotNone(case.opt_report)

    def test_summary_contains_pass_or_fail(self):
        case = differential_test_level("print(1);", level="O1")
        summary = case.summary()
        self.assertTrue("PASS" in summary or "FAIL" in summary)


class TestDiffTestSuite(unittest.TestCase):

    def test_returns_diff_test_suite(self):
        suite = differential_test("print(1);")
        self.assertIsInstance(suite, DiffTestSuite)

    def test_suite_has_four_cases_by_default(self):
        suite = differential_test("print(1);")
        self.assertEqual(len(suite.cases), 4)

    def test_all_levels_in_suite(self):
        suite = differential_test("print(1);")
        levels = [c.level for c in suite.cases]
        self.assertIn("O0", levels)
        self.assertIn("O1", levels)
        self.assertIn("O2", levels)
        self.assertIn("O3", levels)

    def test_custom_levels(self):
        suite = differential_test("print(1);", levels=["O0", "O3"])
        self.assertEqual(len(suite.cases), 2)
        self.assertEqual({c.level for c in suite.cases}, {"O0", "O3"})

    def test_summary_is_string(self):
        suite = differential_test("print(5);")
        summary = suite.summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Differential Testing Report", summary)

    def test_all_passed_property(self):
        suite = differential_test("print(42);")
        self.assertTrue(suite.all_passed)


class TestSemanticsPreservationDiff(unittest.TestCase):
    """
    The definitive correctness test: all programs must pass all four levels.
    These tests confirm that no optimization introduces a semantic difference.
    """

    def test_all_programs_all_levels(self):
        for source in SIMPLE_PROGRAMS:
            suite = differential_test(source)
            for case in suite.cases:
                self.assertTrue(
                    case.passed,
                    f"Differential test FAILED\n"
                    f"Source: {source!r}\n"
                    f"Level: {case.level}\n"
                    f"Reason: {case.failure_reason}\n"
                    f"Error: {case.error}\n"
                    f"Reference: {case.reference_output}\n"
                    f"Optimized: {case.optimized_output}"
                )


class TestDiffTestEdgeCases(unittest.TestCase):

    def test_empty_print_program(self):
        """A program that prints nothing should still produce matching (empty) outputs."""
        source = "int x = 1;"
        suite = differential_test(source)
        for case in suite.cases:
            self.assertEqual(case.reference_output, case.optimized_output,
                f"Level {case.level}: {case.failure_reason}")

    def test_multiple_prints(self):
        source = "print(1);\nprint(2);\nprint(3);"
        suite = differential_test(source)
        for case in suite.cases:
            self.assertTrue(case.passed, f"Level {case.level}: {case.failure_reason}")
            self.assertEqual(case.reference_output, [1, 2, 3])

    def test_loop_with_print(self):
        source = "int i = 0;\nwhile (i < 3) { print(i);\ni = i + 1; }\n"
        suite = differential_test(source)
        for case in suite.cases:
            self.assertTrue(case.passed, f"Level {case.level}: {case.failure_reason}")
            self.assertEqual(case.reference_output, [0, 1, 2])

    def test_nested_arithmetic(self):
        source = "int a = 2 + 3;\nint b = a * 4;\nint c = b - a;\nprint(c);"
        suite = differential_test(source)
        for case in suite.cases:
            self.assertTrue(case.passed, f"Level {case.level}: {case.failure_reason}")

    def test_if_else_semantics(self):
        source = "int x = 5;\nif (1) { x = 10; } else { x = 20; }\nprint(x);"
        suite = differential_test(source)
        for case in suite.cases:
            self.assertTrue(case.passed, f"Level {case.level}: {case.failure_reason}")


if __name__ == "__main__":
    unittest.main()
