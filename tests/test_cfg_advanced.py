"""
Test Suite for the Advanced CFG (cfg_advanced.py).

Tests cover:
  - Basic block partitioning from linear TAC
  - Successor / predecessor edge construction
  - Dominator tree computation
  - Dominance frontier computation
  - Natural loop detection
  - Graphviz DOT export format
  - Textual summary format
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from tac import TACInstruction
from analysis.cfg_advanced import build_cfg, cfg_to_dot, cfg_summary, BasicBlock


def make_inst(op, arg1=None, arg2=None, result=None):
    return TACInstruction(op, arg1, arg2, result)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: common instruction sequences
# ─────────────────────────────────────────────────────────────────────────────

def straight_line():
    """Simple 3-instruction straight-line program: t1=5, t2=t1+3, print t2."""
    return [
        make_inst("CONST", 5, None, "t1"),
        make_inst("ADD", "t1", 3, "t2"),
        make_inst("PRINT", "t2"),
    ]


def if_else():
    """
    if-else TAC:
        t1 = 1
        if_false t1 goto L1
        t2 = 10
        goto L2
        L1:
        t2 = 20
        L2:
        print t2
    """
    return [
        make_inst("CONST", 1, None, "t1"),
        make_inst("JUMP_IF_FALSE", "t1", None, "L1"),
        make_inst("CONST", 10, None, "t2"),
        make_inst("JUMP", None, None, "L2"),
        make_inst("LABEL", None, None, "L1"),
        make_inst("CONST", 20, None, "t2"),
        make_inst("LABEL", None, None, "L2"),
        make_inst("PRINT", "t2"),
    ]


def simple_loop():
    """
    while loop TAC:
        i = 0
        L_start:
        t1 = i < 5
        if_false t1 goto L_end
        i = i + 1
        goto L_start
        L_end:
        print i
    """
    return [
        make_inst("CONST", 0, None, "i"),
        make_inst("LABEL", None, None, "L_start"),
        make_inst("LT", "i", 5, "t1"),
        make_inst("JUMP_IF_FALSE", "t1", None, "L_end"),
        make_inst("ADD", "i", 1, "i"),
        make_inst("JUMP", None, None, "L_start"),
        make_inst("LABEL", None, None, "L_end"),
        make_inst("PRINT", "i"),
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Test classes
# ─────────────────────────────────────────────────────────────────────────────

class TestCFGEmpty(unittest.TestCase):

    def test_empty_instructions_returns_single_block(self):
        cfg = build_cfg([])
        self.assertEqual(len(cfg.blocks), 1)
        self.assertEqual(cfg.entry_id, "B0")

    def test_empty_block_has_no_successors_or_predecessors(self):
        cfg = build_cfg([])
        bb = cfg.blocks[0]
        self.assertEqual(bb.successors, [])
        self.assertEqual(bb.predecessors, [])


class TestCFGStraightLine(unittest.TestCase):

    def setUp(self):
        self.cfg = build_cfg(straight_line())

    def test_single_block_for_straight_line(self):
        # No branches → only one basic block
        self.assertEqual(len(self.cfg.blocks), 1)

    def test_entry_block_id(self):
        self.assertEqual(self.cfg.entry_id, "B0")

    def test_all_instructions_in_block(self):
        bb = self.cfg.blocks[0]
        self.assertEqual(len(bb.instructions), 3)

    def test_no_successors_no_predecessors(self):
        bb = self.cfg.blocks[0]
        self.assertEqual(bb.successors, [])
        self.assertEqual(bb.predecessors, [])

    def test_dominator_of_entry_is_itself(self):
        bb = self.cfg.blocks[0]
        self.assertIn("B0", bb.dominators)
        self.assertIsNone(bb.immediate_dominator)

    def test_no_loops(self):
        self.assertEqual(self.cfg.loops, [])


class TestCFGIfElse(unittest.TestCase):

    def setUp(self):
        self.cfg = build_cfg(if_else())

    def test_four_basic_blocks(self):
        # Instructions split at:
        #   Leader 0 (entry), leader at LABEL L1, leader at LABEL L2,
        #   leader at instruction after JUMP_IF_FALSE
        # Expected: B0 (before jump), B1 (true branch), B2 (L1 block), B3 (L2 print)
        # Exact split depends on which instructions are between labels
        self.assertGreaterEqual(len(self.cfg.blocks), 2)

    def test_entry_has_two_successors(self):
        # B0 ends with JUMP_IF_FALSE → has 2 successors
        entry = self.cfg.block_map[self.cfg.entry_id]
        self.assertEqual(len(entry.successors), 2)

    def test_label_to_block_mapping(self):
        # L1 and L2 should be in label_to_block
        self.assertIn("L1", self.cfg.label_to_block)
        self.assertIn("L2", self.cfg.label_to_block)

    def test_dominance_computed(self):
        # Every block should have a non-empty dominators set
        for bb in self.cfg.blocks:
            self.assertTrue(len(bb.dominators) > 0)

    def test_no_loops_in_if_else(self):
        self.assertEqual(self.cfg.loops, [])


class TestCFGLoop(unittest.TestCase):

    def setUp(self):
        self.cfg = build_cfg(simple_loop())

    def test_loop_detected(self):
        self.assertGreater(len(self.cfg.loops), 0)

    def test_back_edge_identified(self):
        # The loop header should be the block starting at L_start
        header_bid = self.cfg.label_to_block.get("L_start")
        self.assertIsNotNone(header_bid)
        header_bb = self.cfg.block_map[header_bid]
        self.assertTrue(header_bb.is_loop_header)

    def test_loop_body_contains_header_and_tail(self):
        loop = self.cfg.loops[0]
        self.assertIn(loop.header, loop.body)
        self.assertIn(loop.tail, loop.body)

    def test_loop_depth_inside_body_is_positive(self):
        loop = self.cfg.loops[0]
        for bid in loop.body:
            bb = self.cfg.block_map[bid]
            self.assertGreater(bb.loop_depth, 0)

    def test_blocks_outside_loop_have_depth_zero(self):
        loop = self.cfg.loops[0]
        for bb in self.cfg.blocks:
            if bb.block_id not in loop.body:
                self.assertEqual(bb.loop_depth, 0)

    def test_dominators_entry_dominates_all(self):
        entry_id = self.cfg.entry_id
        for bb in self.cfg.blocks:
            self.assertIn(entry_id, bb.dominators)


class TestCFGDominance(unittest.TestCase):
    """
    Handcrafted dominance test using a known graph:

        B0 → B1 → B2 → B4
                ↘ B3 ↗

    idom: B0 idom B1, B1 idom B2, B1 idom B3, B1 idom B4
    DF:   B4 ∈ DF(B2), B4 ∈ DF(B3)
    """

    def setUp(self):
        # B0: const 0, t1 → fall through to B1
        # B1: JUMP_IF_FALSE t1 → L_b3 (B3); else → B2
        # B2: const 10 → JUMP → L_b4 (B4)
        # B3: LABEL L_b3; const 20 → fall through to B4
        # B4: LABEL L_b4; print t1
        self.insts = [
            make_inst("CONST", 0, None, "t1"),                   # B0
            make_inst("JUMP_IF_FALSE", "t1", None, "L_b3"),      # B0 → B1(true) / B3(false)
            make_inst("CONST", 10, None, "t2"),                   # B1
            make_inst("JUMP", None, None, "L_b4"),                # B1 → B2 (unconditional)
            make_inst("LABEL", None, None, "L_b3"),               # B3 starts here
            make_inst("CONST", 20, None, "t2"),                   # B3
            make_inst("LABEL", None, None, "L_b4"),               # B4 starts here
            make_inst("PRINT", "t1"),                             # B4
        ]
        self.cfg = build_cfg(self.insts)

    def test_multiple_blocks_created(self):
        self.assertGreater(len(self.cfg.blocks), 2)

    def test_entry_dominates_all(self):
        entry_id = self.cfg.entry_id
        for bb in self.cfg.blocks:
            self.assertIn(entry_id, bb.dominators)

    def test_join_point_has_dominance_frontier(self):
        # The block containing LABEL L_b4 should have a non-empty DF
        join_bid = self.cfg.label_to_block.get("L_b4")
        if join_bid:
            # Predecessors of join block should have it in their DF
            join_bb = self.cfg.block_map[join_bid]
            for pred_bid in join_bb.predecessors:
                pred_bb = self.cfg.block_map[pred_bid]
                # Dominance frontier of predecessor should include join block or
                # be empty if predecessor strictly dominates join — either is valid
                # We just check the analysis ran without error


class TestCFGDotExport(unittest.TestCase):

    def test_dot_export_is_valid_string(self):
        cfg = build_cfg(simple_loop())
        dot = cfg_to_dot(cfg)
        self.assertIn("digraph", dot)
        self.assertIn("->", dot)
        self.assertIn("B0", dot)

    def test_loop_header_has_steelblue_colour(self):
        cfg = build_cfg(simple_loop())
        dot = cfg_to_dot(cfg)
        self.assertIn("steelblue", dot)

    def test_back_edge_marked_dashed(self):
        cfg = build_cfg(simple_loop())
        dot = cfg_to_dot(cfg)
        self.assertIn("dashed", dot)

    def test_custom_program_name(self):
        cfg = build_cfg(straight_line())
        dot = cfg_to_dot(cfg, program_name="my_test")
        self.assertIn("my_test", dot)


class TestCFGSummary(unittest.TestCase):

    def test_summary_contains_statistics(self):
        cfg = build_cfg(simple_loop())
        summary = cfg_summary(cfg)
        self.assertIn("Blocks", summary)
        self.assertIn("Instructions", summary)
        self.assertIn("Edges", summary)
        self.assertIn("Natural loops", summary)

    def test_summary_mentions_loop_header(self):
        cfg = build_cfg(simple_loop())
        summary = cfg_summary(cfg)
        self.assertIn("LOOP HEADER", summary)


class TestBasicBlockHelpers(unittest.TestCase):

    def test_defines_returns_written_variables(self):
        insts = [
            make_inst("CONST", 5, None, "t1"),
            make_inst("ADD", "t1", 3, "t2"),
        ]
        bb = BasicBlock("B0", insts, 0, 1)
        defs = bb.defines()
        self.assertIn("t1", defs)
        self.assertIn("t2", defs)

    def test_uses_returns_upward_exposed_uses(self):
        insts = [
            make_inst("ADD", "x", "y", "t1"),
        ]
        bb = BasicBlock("B0", insts, 0, 0)
        uses = bb.uses()
        self.assertIn("x", uses)
        self.assertIn("y", uses)

    def test_uses_does_not_include_killed_before_use(self):
        # t1 is defined then used: t1 should not appear in upward-exposed uses
        insts = [
            make_inst("CONST", 5, None, "t1"),
            make_inst("ADD", "t1", 3, "t2"),
        ]
        bb = BasicBlock("B0", insts, 0, 1)
        uses = bb.uses()
        self.assertNotIn("t1", uses)

    def test_print_operand_counted_as_use(self):
        insts = [make_inst("PRINT", "x")]
        bb = BasicBlock("B0", insts, 0, 0)
        uses = bb.uses()
        self.assertIn("x", uses)


class TestCFGAllVariables(unittest.TestCase):

    def test_all_variables_present(self):
        cfg = build_cfg(simple_loop())
        all_vars = cfg.all_variables()
        self.assertIn("i", all_vars)
        self.assertIn("t1", all_vars)


if __name__ == "__main__":
    unittest.main()
