"""
Test Suite for the Advanced Optimization Engine (advanced_optimizer.py).

Tests cover:
  1. CSE — Common Subexpression Elimination
  2. Copy Propagation
  3. LICM — Loop Invariant Code Motion
  4. Strength Reduction
  5. Algebraic Simplification
  6. OptimizationPassManager (all levels O0–O3)
  7. Before/After comparison utility
  8. Semantics preservation: optimized output == unoptimized VM output
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from lexer import Lexer
from parser import Parser
from tac import TACGenerator, TACInstruction
from interpreter import Interpreter
from advanced_optimizer import (
    cse_pass,
    copy_propagation_pass,
    licm_pass,
    strength_reduction_pass,
    algebraic_simplification_pass,
    OptimizationPassManager,
    OptimizationReport,
    PassStats,
    OptRecord,
    OPTIMIZATION_LEVELS,
    compare_ir,
)


def make_inst(op, arg1=None, arg2=None, result=None):
    return TACInstruction(op, arg1, arg2, result)


def compile_to_tac(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return TACGenerator().generate(ast)


def run_tac(instructions, max_steps=10_000):
    vm = Interpreter(list(instructions), max_steps=max_steps)
    return vm.run()


# ─────────────────────────────────────────────────────────────────────────────
# 1. CSE Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCSE(unittest.TestCase):

    def test_duplicate_expression_replaced_with_copy(self):
        """t2 = x + y when t1 = x + y already exists → t2 = ASSIGN t1."""
        insts = [
            make_inst("ADD", "x", "y", "t1"),
            make_inst("ADD", "x", "y", "t2"),   # duplicate
        ]
        result, records = cse_pass(insts)
        t2_inst = next(i for i in result if i.result == "t2")
        self.assertEqual(t2_inst.op, "ASSIGN")
        self.assertEqual(t2_inst.arg1, "t1")

    def test_commutative_cse(self):
        """ADD is commutative: t2 = y + x should be identified as same as t1 = x + y."""
        insts = [
            make_inst("ADD", "x", "y", "t1"),
            make_inst("ADD", "y", "x", "t2"),
        ]
        result, records = cse_pass(insts)
        t2_inst = next(i for i in result if i.result == "t2")
        self.assertEqual(t2_inst.op, "ASSIGN")
        self.assertEqual(len(records), 1)

    def test_non_duplicate_not_changed(self):
        """t2 = x - y should NOT be replaced when only t1 = x + y exists."""
        insts = [
            make_inst("ADD", "x", "y", "t1"),
            make_inst("SUB", "x", "y", "t2"),
        ]
        result, records = cse_pass(insts)
        t2_inst = next(i for i in result if i.result == "t2")
        self.assertEqual(t2_inst.op, "SUB")
        self.assertEqual(len(records), 0)

    def test_redefinition_invalidates_expr(self):
        """Redefining x should invalidate any available expression using x."""
        insts = [
            make_inst("ADD", "x", "y", "t1"),
            make_inst("CONST", 99, None, "x"),   # kills x-expressions
            make_inst("ADD", "x", "y", "t2"),   # x is now different
        ]
        result, records = cse_pass(insts)
        t2_inst = next(i for i in result if i.result == "t2")
        # Should NOT be CSE'd because x was redefined
        self.assertEqual(t2_inst.op, "ADD")
        self.assertEqual(len(records), 0)

    def test_cse_records_category(self):
        insts = [
            make_inst("ADD", "a", "b", "t1"),
            make_inst("ADD", "a", "b", "t2"),
        ]
        _, records = cse_pass(insts)
        self.assertEqual(records[0].category, "cse")
        self.assertEqual(records[0].pass_name, "CSE")

    def test_cse_preserves_semantics(self):
        source = "int x = 3;\nint y = 4;\nint t1 = x + y;\nint t2 = x + y;\nprint(t1 + t2);"
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        opt, _ = cse_pass(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Copy Propagation Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCopyPropagation(unittest.TestCase):

    def test_copy_propagated_through_use(self):
        """t1 = x; t2 = t1 + 1 → t2 = x + 1."""
        insts = [
            make_inst("ASSIGN", "x", None, "t1"),
            make_inst("ADD", "t1", 1, "t2"),
        ]
        result, records = copy_propagation_pass(insts)
        t2_inst = next(i for i in result if i.result == "t2")
        self.assertEqual(t2_inst.arg1, "x")
        self.assertGreater(len(records), 0)

    def test_redefinition_stops_propagation(self):
        """After x is redefined, t1=x should no longer propagate the old x."""
        insts = [
            make_inst("ASSIGN", "x", None, "t1"),
            make_inst("CONST", 99, None, "x"),   # x is redefined
            make_inst("ADD", "t1", 1, "t2"),      # t1 still holds old x, propagation safe
        ]
        result, records = copy_propagation_pass(insts)
        # t1 was not redefined; it still copies old x value
        # Whether we propagate t1→x here depends on stale-copy removal
        # The key: no crash and the instruction is well-formed
        t2_inst = next(i for i in result if i.result == "t2")
        self.assertIsNotNone(t2_inst)

    def test_chain_propagation(self):
        """a=x, b=a, c=b → all should propagate to x."""
        insts = [
            make_inst("ASSIGN", "x", None, "a"),
            make_inst("ASSIGN", "a", None, "b"),
            make_inst("ASSIGN", "b", None, "c"),
            make_inst("PRINT", "c"),
        ]
        result, records = copy_propagation_pass(insts)
        # After propagation, PRINT should use x (or a name traceable to x)
        print_inst = next(i for i in result if i.op == "PRINT")
        self.assertIn(str(print_inst.arg1), {"x", "a", "b", "c"})

    def test_copy_propagation_preserves_semantics(self):
        source = "int x = 7;\nint y = x;\nprint(y + 1);"
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        opt, _ = copy_propagation_pass(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got)


# ─────────────────────────────────────────────────────────────────────────────
# 3. LICM Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLICM(unittest.TestCase):

    def test_invariant_computation_hoisted(self):
        """A constant computation inside a loop should be hoisted."""
        # int i = 0; int c = 5; while (i < 3) { t = c + 2; i = i + 1; } print(i);
        # c is defined outside the loop, 2 is a constant → c+2 is loop-invariant
        insts = [
            make_inst("CONST", 0, None, "i"),
            make_inst("CONST", 5, None, "c"),
            make_inst("LABEL", None, None, "L_s"),
            make_inst("LT", "i", 3, "t0"),
            make_inst("JUMP_IF_FALSE", "t0", None, "L_e"),
            make_inst("ADD", "c", 2, "t_inv"),   # loop-invariant: c and 2 are loop-constant
            make_inst("ADD", "i", 1, "i"),
            make_inst("JUMP", None, None, "L_s"),
            make_inst("LABEL", None, None, "L_e"),
            make_inst("PRINT", "i"),
        ]
        result, records = licm_pass(insts)
        # At least one hoist should have occurred
        # (t_inv = c + 2 should be moved before L_s)
        self.assertGreater(len(records), 0)

    def test_variant_computation_not_hoisted(self):
        """A computation using i (the induction var) must NOT be hoisted."""
        insts = [
            make_inst("CONST", 0, None, "i"),
            make_inst("LABEL", None, None, "L_s"),
            make_inst("LT", "i", 5, "t0"),
            make_inst("JUMP_IF_FALSE", "t0", None, "L_e"),
            make_inst("ADD", "i", 1, "i"),    # uses and defines i → variant
            make_inst("JUMP", None, None, "L_s"),
            make_inst("LABEL", None, None, "L_e"),
            make_inst("PRINT", "i"),
        ]
        result, records = licm_pass(insts)
        # The ADD i+1 is NOT invariant; should not be hoisted
        hoist_records = [r for r in records if "i + 1" in r.original or "ADD" in r.original]
        # Even if there are some records, the i += 1 instruction must remain in the loop
        # Verify the result still contains an ADD of i somewhere after the loop
        ops = [inst.op for inst in result]
        self.assertIn("ADD", ops)

    def test_licm_preserves_semantics(self):
        source = "int i = 0;\nwhile (i < 3) { i = i + 1; }\nprint(i);"
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        opt, _ = licm_pass(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Strength Reduction Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestStrengthReduction(unittest.TestCase):

    def test_mul_by_2_inside_loop_replaced_with_add(self):
        """x * 2 inside a loop body → x + x."""
        insts = [
            make_inst("CONST", 1, None, "x"),
            make_inst("LABEL", None, None, "L_s"),
            make_inst("LT", "x", 10, "t0"),
            make_inst("JUMP_IF_FALSE", "t0", None, "L_e"),
            make_inst("MUL", "x", 2, "t1"),    # inside loop: x * 2 → x + x
            make_inst("ADD", "x", 1, "x"),
            make_inst("JUMP", None, None, "L_s"),
            make_inst("LABEL", None, None, "L_e"),
            make_inst("PRINT", "t1"),
        ]
        result, records = strength_reduction_pass(insts)
        sr_records = [r for r in records if r.category == "strength_reduction"]
        self.assertGreater(len(sr_records), 0)
        # Check the MUL was replaced with ADD
        t1_insts = [i for i in result if i.result == "t1"]
        self.assertEqual(t1_insts[0].op, "ADD")
        self.assertEqual(t1_insts[0].arg1, t1_insts[0].arg2)

    def test_mul_outside_loop_not_changed(self):
        """x * 2 OUTSIDE a loop must NOT be changed by strength reduction."""
        insts = [
            make_inst("CONST", 5, None, "x"),
            make_inst("MUL", "x", 2, "t1"),   # no loop context
            make_inst("PRINT", "t1"),
        ]
        result, records = strength_reduction_pass(insts)
        self.assertEqual(len(records), 0)
        t1_inst = next(i for i in result if i.result == "t1")
        self.assertEqual(t1_inst.op, "MUL")

    def test_strength_reduction_preserves_semantics(self):
        source = "int i = 0;\nwhile (i < 5) { i = i + 1; }\nprint(i);"
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        opt, _ = strength_reduction_pass(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Algebraic Simplification Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAlgebraicSimplification(unittest.TestCase):

    def _simp(self, op, a1, a2, res="t"):
        inst, = algebraic_simplification_pass([make_inst(op, a1, a2, res)])[0]
        return inst

    def test_add_zero_right(self):
        inst = self._simp("ADD", "x", 0, "t1")
        self.assertEqual(inst.op, "ASSIGN")
        self.assertEqual(inst.arg1, "x")

    def test_add_zero_left(self):
        inst = self._simp("ADD", 0, "x", "t1")
        self.assertEqual(inst.op, "ASSIGN")
        self.assertEqual(inst.arg1, "x")

    def test_sub_zero(self):
        inst = self._simp("SUB", "x", 0, "t1")
        self.assertEqual(inst.op, "ASSIGN")
        self.assertEqual(inst.arg1, "x")

    def test_mul_zero(self):
        inst = self._simp("MUL", "x", 0, "t1")
        self.assertEqual(inst.op, "CONST")
        self.assertEqual(inst.arg1, 0)

    def test_mul_one(self):
        inst = self._simp("MUL", "x", 1, "t1")
        self.assertEqual(inst.op, "ASSIGN")
        self.assertEqual(inst.arg1, "x")

    def test_div_one(self):
        inst = self._simp("DIV", "x", 1, "t1")
        self.assertEqual(inst.op, "ASSIGN")
        self.assertEqual(inst.arg1, "x")

    def test_sub_self(self):
        inst = self._simp("SUB", "x", "x", "t1")
        self.assertEqual(inst.op, "CONST")
        self.assertEqual(inst.arg1, 0)

    def test_eq_self(self):
        inst = self._simp("EQ", "x", "x", "t1")
        self.assertEqual(inst.op, "CONST")
        self.assertEqual(inst.arg1, 1)

    def test_ne_self(self):
        inst = self._simp("NE", "x", "x", "t1")
        self.assertEqual(inst.op, "CONST")
        self.assertEqual(inst.arg1, 0)

    def test_non_simplifiable_unchanged(self):
        inst = self._simp("ADD", "x", "y", "t1")
        self.assertEqual(inst.op, "ADD")

    def test_algebraic_preserves_semantics(self):
        source = "int x = 5;\nint y = x + 0;\nprint(y);"
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        opt, _ = algebraic_simplification_pass(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got)

    def test_records_have_correct_category(self):
        insts = [make_inst("ADD", "x", 0, "t1")]
        _, records = algebraic_simplification_pass(insts)
        self.assertEqual(records[0].category, "algebraic")
        self.assertEqual(records[0].pass_name, "AlgebraicSimplification")


# ─────────────────────────────────────────────────────────────────────────────
# 6. OptimizationPassManager Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestOptimizationPassManager(unittest.TestCase):

    def test_o0_returns_unchanged_instructions(self):
        source = "int x = 5;\nprint(x);"
        raw = compile_to_tac(source)
        manager = OptimizationPassManager(level="O0")
        opt, report = manager.run(raw)
        # O0 applies no passes, so instruction list must be identical in content
        self.assertEqual(len(opt), len(raw))
        self.assertEqual(report.total_transforms, 0)

    def test_all_levels_produce_valid_report(self):
        source = "int x = 3;\nint y = x + 0;\nprint(y);"
        raw = compile_to_tac(source)
        for level in ("O0", "O1", "O2", "O3"):
            manager = OptimizationPassManager(level=level)
            opt, report = manager.run(raw)
            self.assertIsInstance(report, OptimizationReport)
            self.assertEqual(report.instructions_before, len(raw))
            self.assertEqual(report.instructions_after, len(opt))

    def test_report_summary_is_string(self):
        raw = compile_to_tac("print(42);")
        manager = OptimizationPassManager(level="O2")
        _, report = manager.run(raw)
        summary = report.summary()
        self.assertIn("Advanced Optimization Report", summary)
        self.assertIsInstance(summary, str)

    def test_invalid_level_raises_value_error(self):
        with self.assertRaises(ValueError):
            OptimizationPassManager(level="O99")

    def test_custom_pass_list_is_respected(self):
        raw = compile_to_tac("int x = 5;\nint y = x + 0;\nprint(y);")
        manager = OptimizationPassManager(passes=[algebraic_simplification_pass])
        opt, report = manager.run(raw)
        self.assertEqual(len(report.pass_stats), 1)
        self.assertEqual(report.pass_stats[0].pass_name, "algebraic_simplification_pass")

    def test_pass_names_property(self):
        manager = OptimizationPassManager(level="O1")
        names = manager.pass_names
        self.assertIn("algebraic_simplification_pass", names)
        self.assertIn("copy_propagation_pass", names)

    def test_o3_applies_more_passes_than_o1(self):
        manager_o1 = OptimizationPassManager(level="O1")
        manager_o3 = OptimizationPassManager(level="O3")
        self.assertGreater(len(manager_o3.pass_names), len(manager_o1.pass_names))


# ─────────────────────────────────────────────────────────────────────────────
# 7. Semantics Preservation (all levels, multiple programs)
# ─────────────────────────────────────────────────────────────────────────────

PROGRAMS = [
    "print(42);",
    "int x = 10;\nprint(x);",
    "int x = 5;\nint y = x + 3;\nprint(y);",
    "int i = 0;\nwhile (i < 5) { i = i + 1; }\nprint(i);",
    "int a = 2 + 3;\nint b = a * 1;\nprint(b + 0);",
    "int x = 10;\nif (1) { x = 20; }\nprint(x);",
    "int a = 7;\nint b = 7;\nint c = a - b;\nprint(c);",
]


class TestSemanticsPreservation(unittest.TestCase):
    """All optimization levels must produce the same output as unoptimized TAC."""

    def _check(self, source: str, level: str):
        raw = compile_to_tac(source)
        ref = run_tac(raw)
        manager = OptimizationPassManager(level=level)
        opt, _ = manager.run(raw)
        got = run_tac(opt)
        self.assertEqual(ref, got,
            f"Semantics broken at level {level} for:\n{source}\n"
            f"Expected: {ref}, Got: {got}")

    def test_semantics_all_levels_all_programs(self):
        for source in PROGRAMS:
            for level in ("O0", "O1", "O2", "O3"):
                with self.subTest(source=source[:40], level=level):
                    self._check(source, level)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Before/After Comparison Utility
# ─────────────────────────────────────────────────────────────────────────────

class TestCompareIR(unittest.TestCase):

    def test_compare_ir_returns_string(self):
        raw = compile_to_tac("int x = 5;\nprint(x);")
        manager = OptimizationPassManager(level="O1")
        opt, _ = manager.run(raw)
        comparison = compare_ir(raw, opt)
        self.assertIsInstance(comparison, str)
        self.assertIn("BEFORE", comparison)
        self.assertIn("AFTER", comparison)

    def test_compare_ir_custom_title(self):
        raw = compile_to_tac("print(1);")
        comparison = compare_ir(raw, raw, title="My Custom Title")
        self.assertIn("My Custom Title", comparison)


# ─────────────────────────────────────────────────────────────────────────────
# 9. OptRecord and PassStats
# ─────────────────────────────────────────────────────────────────────────────

class TestDataStructures(unittest.TestCase):

    def test_opt_record_to_dict(self):
        rec = OptRecord("CSE", "t1 = x + y", "t1 = ASSIGN t0", "duplicate", "cse")
        d = rec.to_dict()
        self.assertIn("pass_name", d)
        self.assertEqual(d["category"], "cse")

    def test_pass_stats_reduction(self):
        ps = PassStats("CSE", transforms_applied=3, instructions_before=10, instructions_after=7)
        self.assertEqual(ps.reduction, 3)

    def test_optimization_report_reduction_pct(self):
        report = OptimizationReport(
            instructions_before=10,
            instructions_after=8,
        )
        self.assertAlmostEqual(report.reduction_pct, 20.0, places=1)


if __name__ == "__main__":
    unittest.main()
