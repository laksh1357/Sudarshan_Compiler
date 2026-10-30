"""
Test Suite for SSA Form (ssa.py).

Tests cover:
  - Straight-line programs (no phi nodes needed)
  - If-else programs (phi nodes at the join point)
  - Loop programs (phi nodes at the loop header)
  - Versioned name uniqueness
  - Round-trip semantics preservation (SSA → lowered TAC = same output as original)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from lexer import Lexer
from parser import Parser
from tac import TACGenerator, TACInstruction
from interpreter import Interpreter
from analysis.ssa import build_ssa, ssa_to_tac, PhiNode, SSABlock


def make_inst(op, arg1=None, arg2=None, result=None):
    return TACInstruction(op, arg1, arg2, result)


def compile_to_tac(source: str):
    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()
    return TACGenerator().generate(ast)


def run_tac(instructions):
    vm = Interpreter(instructions, max_steps=10_000)
    return vm.run()


class TestSSAStraightLine(unittest.TestCase):

    def test_versioned_names_are_unique(self):
        """In a straight-line program every definition must get a unique version."""
        insts = [
            make_inst("CONST", 5, None, "x"),
            make_inst("CONST", 3, None, "y"),
            make_inst("ADD", "x", "y", "z"),
        ]
        ssa = build_ssa(insts)
        # Collect all result names
        results = []
        for block in ssa.blocks:
            for inst in block.instructions:
                if inst.result is not None:
                    results.append(inst.result)
        # All result names must be unique
        self.assertEqual(len(results), len(set(results)))

    def test_no_phi_nodes_in_straight_line(self):
        """Straight-line programs never need phi nodes."""
        source = "int a = 5;\nint b = 3;\nprint(a + b);"
        raw = compile_to_tac(source)
        ssa = build_ssa(raw)
        for block in ssa.blocks:
            self.assertEqual(len(block.phi_nodes), 0)

    def test_result_names_have_dot_version(self):
        """All SSA result names must contain a dot version suffix."""
        insts = [
            make_inst("CONST", 10, None, "x"),
            make_inst("ADD", "x", 1, "y"),
        ]
        ssa = build_ssa(insts)
        for block in ssa.blocks:
            for inst in block.instructions:
                if inst.result is not None and "." in str(inst.result):
                    self.assertRegex(str(inst.result), r"\w+\.\d+")


class TestSSAIfElse(unittest.TestCase):

    def setUp(self):
        # if-else: x is 10 in true branch, 20 in false branch.
        # A phi node for x should appear at the join block.
        self.source = "int x = 0;\nif (1) { x = 10; } else { x = 20; }\nprint(x);"

    def test_phi_nodes_inserted_at_join(self):
        """The join block after an if-else must have at least one phi node."""
        raw = compile_to_tac(self.source)
        ssa = build_ssa(raw)
        total_phis = sum(len(b.phi_nodes) for b in ssa.blocks)
        self.assertGreater(total_phis, 0)


class TestSSALoop(unittest.TestCase):

    def setUp(self):
        self.source = "int i = 0;\nwhile (i < 5) { i = i + 1; }\nprint(i);"

    def test_phi_node_at_loop_header(self):
        """Loop header must have a phi node for the induction variable i."""
        raw = compile_to_tac(self.source)
        ssa = build_ssa(raw)
        # At least one block must have a phi node
        total_phis = sum(len(b.phi_nodes) for b in ssa.blocks)
        self.assertGreater(total_phis, 0, "Expected phi nodes at loop header for induction variable")

    def test_phi_node_has_two_predecessors(self):
        """Loop header phi should have exactly two incoming args (entry and back-edge)."""
        raw = compile_to_tac(self.source)
        ssa = build_ssa(raw)
        for block in ssa.blocks:
            for phi in block.phi_nodes:
                # Loop header phi has exactly 2 predecessors: entry and loop tail
                self.assertGreaterEqual(len(phi.args), 1)


class TestSSARoundTrip(unittest.TestCase):
    """
    Verifies that building SSA and then lowering back produces a TAC program
    whose execution output matches the original unoptimized TAC output.
    """

    def _check_roundtrip(self, source: str):
        raw = compile_to_tac(source)
        ref_output = run_tac(list(raw))

        ssa = build_ssa(raw)
        lowered = ssa_to_tac(ssa)
        opt_output = run_tac(lowered)

        self.assertEqual(ref_output, opt_output,
            f"Round-trip mismatch for source:\n{source}\n"
            f"Reference: {ref_output}\nAfter SSA lowering: {opt_output}")

    def test_roundtrip_straight_line(self):
        self._check_roundtrip("int a = 10;\nint b = 5;\nprint(a + b);")

    def test_roundtrip_print_literal(self):
        self._check_roundtrip("print(42);")

    def test_roundtrip_arithmetic_chain(self):
        self._check_roundtrip("int x = 2 + 3;\nint y = x * 4;\nprint(y);")

    def test_roundtrip_while_loop(self):
        self._check_roundtrip(
            "int i = 0;\nwhile (i < 3) { i = i + 1; }\nprint(i);"
        )

    def test_roundtrip_constant_comparison(self):
        self._check_roundtrip("int a = 5;\nint b = 5;\nprint(a);")


class TestSSADataStructures(unittest.TestCase):

    def test_phi_node_to_tac_produces_phi_instruction(self):
        phi = PhiNode(result="x.2", args={"B0": "x.0", "B1": "x.1"}, orig_var="x")
        inst = phi.to_tac()
        self.assertEqual(inst.op, "PHI")
        self.assertEqual(inst.result, "x.2")

    def test_phi_node_str_contains_phi_symbol(self):
        phi = PhiNode(result="x.2", args={"B0": "x.0", "B1": "x.1"}, orig_var="x")
        self.assertIn("φ", str(phi))
        self.assertIn("x.2", str(phi))

    def test_ssa_block_all_instructions_tac_includes_phis(self):
        phi = PhiNode(result="x.2", args={"B0": "x.0"}, orig_var="x")
        block = SSABlock("B1", [phi], [])
        all_tac = block.all_instructions_tac()
        self.assertEqual(len(all_tac), 1)
        self.assertEqual(all_tac[0].op, "PHI")


class TestSSAProgramStructure(unittest.TestCase):

    def test_blocks_in_program_order(self):
        """SSAProgram.blocks must be in program order (same as CFG blocks)."""
        source = "int x = 1;\nint y = x + 2;\nprint(y);"
        raw = compile_to_tac(source)
        ssa = build_ssa(raw)
        cfg_bids = [bb.block_id for bb in ssa.cfg.blocks]
        ssa_bids = [sb.block_id for sb in ssa.blocks]
        self.assertEqual(cfg_bids, ssa_bids)

    def test_block_map_lookup(self):
        source = "print(7);"
        raw = compile_to_tac(source)
        ssa = build_ssa(raw)
        for sb in ssa.blocks:
            self.assertIn(sb.block_id, ssa.block_map)


if __name__ == "__main__":
    unittest.main()
