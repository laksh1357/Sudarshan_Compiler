"""
Advanced Control Flow Graph (CFG) Module for Sudarshan Compiler.

Builds a CFG from linear TAC instructions, then computes:
  1. Dominator tree (iterative data-flow algorithm)
  2. Dominance frontiers (for SSA Phi-node placement)
  3. Natural loops (back-edge detection, loop headers, loop bodies)
  4. Graphviz DOT export for visual inspection
  5. Textual summary with statistics

This module is fully independent of the existing security/cfg.py; it builds on
the same TAC data structures but provides richer analyses needed for SSA and the
advanced optimization engine.

Design principles:
  - Pure functions where possible; no mutation of TACInstruction objects
  - Deterministic output (sorted iterations over frozen sets)
  - Complete correctness — every algorithm reference is cited inline
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterator, List, Optional, Set, Tuple

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tac import TACInstruction


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

@dataclass
class BasicBlock:
    """
    A maximal straight-line sequence of TAC instructions.

    A new basic block starts at:
      - Index 0 (program entry)
      - Any instruction that is a branch target (LABEL instruction)
      - Any instruction immediately following a branch (JUMP / JUMP_IF_FALSE)
    """

    block_id: str                            # Unique identifier: "B0", "B1", …
    instructions: List[TACInstruction]       # Instructions belonging to this block (in order)
    first_index: int                         # Index of first instruction in original flat list
    last_index: int                          # Index of last  instruction in original flat list
    successors: List[str] = field(default_factory=list)    # Block IDs of control-flow successors
    predecessors: List[str] = field(default_factory=list)  # Block IDs of control-flow predecessors
    # Dominator analysis results (filled after build_cfg returns)
    dominators: FrozenSet[str] = field(default_factory=frozenset)
    immediate_dominator: Optional[str] = None
    dominance_frontier: Set[str] = field(default_factory=set)
    # Loop analysis
    is_loop_header: bool = False
    loop_depth: int = 0
    back_edge_sources: List[str] = field(default_factory=list)

    # -----------------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------------

    def defines(self) -> Set[str]:
        """Variables/temporaries written in this block (excluding LABEL pseudo-def)."""
        defs: Set[str] = set()
        for inst in self.instructions:
            if inst.result and inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT"):
                defs.add(str(inst.result))
        return defs

    def uses(self) -> Set[str]:
        """Variables/temporaries read in this block (upward-exposed uses)."""
        used: Set[str] = set()
        killed: Set[str] = set()
        for inst in self.instructions:
            for operand in (inst.arg1, inst.arg2):
                if isinstance(operand, str) and operand not in killed:
                    used.add(operand)
            if inst.result and inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT"):
                killed.add(str(inst.result))
            # JUMP_IF_FALSE also reads arg1
            if inst.op == "JUMP_IF_FALSE" and isinstance(inst.arg1, str):
                if inst.arg1 not in killed:
                    used.add(inst.arg1)
            if inst.op == "PRINT" and isinstance(inst.arg1, str):
                if inst.arg1 not in killed:
                    used.add(inst.arg1)
        return used

    def __hash__(self) -> int:
        return hash(self.block_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BasicBlock) and self.block_id == other.block_id


@dataclass
class ControlFlowGraph:
    """
    Fully-analysed Control Flow Graph for a flat TAC instruction sequence.

    Fields are set by build_cfg() after the complete analysis pipeline.
    """

    blocks: List[BasicBlock]                      # In program order
    entry_id: str                                  # block_id of entry block (always "B0")
    block_map: Dict[str, BasicBlock]               # block_id → BasicBlock
    label_to_block: Dict[str, str]                 # TAC label name → block_id
    # Loop information
    loops: List["NaturalLoop"] = field(default_factory=list)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def block(self, bid: str) -> BasicBlock:
        return self.block_map[bid]

    def all_variables(self) -> Set[str]:
        """All distinct names that appear as result/arg in any block."""
        names: Set[str] = set()
        for bb in self.blocks:
            for inst in bb.instructions:
                for x in (inst.arg1, inst.arg2, inst.result):
                    if isinstance(x, str):
                        names.add(x)
        return names

    def postorder(self) -> Iterator[BasicBlock]:
        """Post-order DFS traversal (used by dominator algorithm)."""
        visited: Set[str] = set()
        order: List[BasicBlock] = []

        def dfs(bid: str) -> None:
            if bid in visited:
                return
            visited.add(bid)
            for s in self.block_map[bid].successors:
                dfs(s)
            order.append(self.block_map[bid])

        dfs(self.entry_id)
        return iter(order)

    def reverse_postorder(self) -> List[BasicBlock]:
        return list(reversed(list(self.postorder())))

    def __repr__(self) -> str:
        return f"<CFG blocks={len(self.blocks)} loops={len(self.loops)}>"


@dataclass
class NaturalLoop:
    """
    A natural loop defined by a back edge (tail → header).

    Attributes:
        header: Block ID of the loop header (dominator of tail).
        tail: Block ID of the block that has the back-edge to header.
        body: Set of block IDs in the loop (includes header and tail).
    """

    header: str
    tail: str
    body: Set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# CFG Construction
# ---------------------------------------------------------------------------

def _identify_leaders(instructions: List[TACInstruction]) -> Tuple[Set[int], Dict[str, int]]:
    """
    Identify leader instruction indices and build a label→index map.

    Leaders:
      - Index 0 is always a leader.
      - The instruction immediately following a JUMP or JUMP_IF_FALSE is a leader.
      - Any instruction that is the target of a JUMP/JUMP_IF_FALSE is a leader
        (identified by preceding LABEL instructions).
    """
    leaders: Set[int] = {0}
    label_indices: Dict[str, int] = {}

    for idx, inst in enumerate(instructions):
        if inst.op == "LABEL" and inst.result is not None:
            label_indices[str(inst.result)] = idx
            leaders.add(idx)
        if inst.op in ("JUMP", "JUMP_IF_FALSE"):
            if idx + 1 < len(instructions):
                leaders.add(idx + 1)

    # Second pass: add jump targets that we now know about
    for inst in instructions:
        if inst.op in ("JUMP", "JUMP_IF_FALSE") and inst.result is not None:
            target = label_indices.get(str(inst.result))
            if target is not None:
                leaders.add(target)

    return leaders, label_indices


def _build_blocks(
    instructions: List[TACInstruction],
    leaders: Set[int],
) -> Tuple[List[BasicBlock], Dict[int, str]]:
    """
    Partition instructions into BasicBlock objects.

    Returns:
        blocks: List of BasicBlock in program order.
        index_to_bid: Maps each instruction index to its block_id.
    """
    sorted_leaders = sorted(leaders)
    blocks: List[BasicBlock] = []
    index_to_bid: Dict[int, str] = {}

    for pos, start in enumerate(sorted_leaders):
        end = sorted_leaders[pos + 1] if pos + 1 < len(sorted_leaders) else len(instructions)
        block_insts = [instructions[i] for i in range(start, end)]
        bid = f"B{pos}"
        bb = BasicBlock(
            block_id=bid,
            instructions=block_insts,
            first_index=start,
            last_index=end - 1,
        )
        blocks.append(bb)
        for i in range(start, end):
            index_to_bid[i] = bid

    return blocks, index_to_bid


def _connect_edges(
    blocks: List[BasicBlock],
    block_map: Dict[str, BasicBlock],
    label_to_block: Dict[str, str],
) -> None:
    """
    Wire up successor/predecessor edges between basic blocks.

    Rules (applied to the last instruction of each block):
      - JUMP → unconditional branch to target block only
      - JUMP_IF_FALSE → conditional branch: true path = next block,
                        false path = target block
      - Otherwise → fall through to the next block in program order
    """
    for pos, bb in enumerate(blocks):
        last = bb.instructions[-1]

        if last.op == "JUMP":
            target_bid = label_to_block.get(str(last.result))
            if target_bid:
                bb.successors.append(target_bid)

        elif last.op == "JUMP_IF_FALSE":
            # False branch → jump target
            target_bid = label_to_block.get(str(last.result))
            if target_bid:
                bb.successors.append(target_bid)
            # True branch → fall through
            if pos + 1 < len(blocks):
                fall_bid = blocks[pos + 1].block_id
                if fall_bid not in bb.successors:
                    bb.successors.append(fall_bid)

        else:
            # Fall through
            if pos + 1 < len(blocks):
                bb.successors.append(blocks[pos + 1].block_id)

    # Build predecessor lists
    for bb in blocks:
        for succ_bid in bb.successors:
            succ = block_map[succ_bid]
            if bb.block_id not in succ.predecessors:
                succ.predecessors.append(bb.block_id)


# ---------------------------------------------------------------------------
# Dominator Analysis (Cooper, Harvey, Kennedy 2001 — simple iterative)
# Reference: "A Simple, Fast Dominance Algorithm", Software Practice & Experience
# ---------------------------------------------------------------------------

def _compute_dominators(cfg: ControlFlowGraph) -> None:
    """
    Compute the immediate dominator (idom) for every block using the
    Cooper/Harvey/Kennedy reverse-post-order iterative algorithm.

    Sets bb.immediate_dominator for every non-entry block.
    """
    rpo = cfg.reverse_postorder()
    rpo_index: Dict[str, int] = {bb.block_id: i for i, bb in enumerate(rpo)}
    idom: Dict[str, Optional[str]] = {bb.block_id: None for bb in rpo}
    entry = cfg.entry_id
    idom[entry] = entry

    def intersect(b1: str, b2: str) -> str:
        finger1, finger2 = b1, b2
        while finger1 != finger2:
            while rpo_index[finger1] > rpo_index[finger2]:
                finger1 = idom[finger1]  # type: ignore[assignment]
            while rpo_index[finger2] > rpo_index[finger1]:
                finger2 = idom[finger2]  # type: ignore[assignment]
        return finger1

    changed = True
    while changed:
        changed = False
        for bb in rpo:
            if bb.block_id == entry:
                continue
            # Processed predecessors (those with an idom already set)
            processed = [p for p in bb.predecessors if idom[p] is not None]
            if not processed:
                continue
            new_idom = processed[0]
            for pred in processed[1:]:
                new_idom = intersect(pred, new_idom)
            if idom[bb.block_id] != new_idom:
                idom[bb.block_id] = new_idom
                changed = True

    for bb in rpo:
        if bb.block_id != entry:
            bb.immediate_dominator = idom[bb.block_id]

    # Compute full dominator sets using the idom tree
    def doms_of(bid: str) -> FrozenSet[str]:
        result: Set[str] = {bid}
        cur = bid
        while idom[cur] is not None and idom[cur] != cur:
            cur = idom[cur]  # type: ignore[assignment]
            result.add(cur)
        result.add(entry)
        return frozenset(result)

    for bb in cfg.blocks:
        bb.dominators = doms_of(bb.block_id)


def _compute_dominance_frontiers(cfg: ControlFlowGraph) -> None:
    """
    Compute the dominance frontier (DF) for every block.

    Algorithm (Cooper et al.):
      For each join node j (pred count ≥ 2):
          for each predecessor p of j:
              runner ← p
              while runner ≠ idom(j):
                  DF(runner) ∪= {j}
                  runner ← idom(runner)
    """
    for bb in cfg.blocks:
        bb.dominance_frontier = set()

    for bb in cfg.blocks:
        if len(bb.predecessors) >= 2:
            for pred_bid in bb.predecessors:
                runner = pred_bid
                idom_j = bb.immediate_dominator
                while runner != idom_j and runner is not None:
                    cfg.block_map[runner].dominance_frontier.add(bb.block_id)
                    runner = cfg.block_map[runner].immediate_dominator  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Loop Analysis (Natural Loops via back-edge detection)
# Reference: "Compilers: Principles, Techniques, and Tools" §8.4
# ---------------------------------------------------------------------------

def _compute_loops(cfg: ControlFlowGraph) -> None:
    """
    Detect natural loops by identifying back edges.

    A back edge is an edge n → h where h dominates n.
    For each back edge (n → h):
      1. Mark h as the loop header.
      2. Find all blocks that can reach n without going through h (loop body).

    Sets bb.is_loop_header, bb.back_edge_sources, bb.loop_depth on each block.
    """
    loops: List[NaturalLoop] = []
    back_edges: List[Tuple[str, str]] = []   # (tail, header)

    for bb in cfg.blocks:
        for succ_bid in bb.successors:
            succ = cfg.block_map[succ_bid]
            # Back edge: succ dominates bb
            if succ_bid in bb.dominators:
                back_edges.append((bb.block_id, succ_bid))

    for tail, header in back_edges:
        # Find loop body: blocks that can reach tail from header without leaving header
        body: Set[str] = {header, tail}
        worklist = [tail]
        while worklist:
            node = worklist.pop()
            for pred in cfg.block_map[node].predecessors:
                if pred not in body:
                    body.add(pred)
                    worklist.append(pred)

        loop = NaturalLoop(header=header, tail=tail, body=body)
        loops.append(loop)

        header_block = cfg.block_map[header]
        header_block.is_loop_header = True
        if tail not in header_block.back_edge_sources:
            header_block.back_edge_sources.append(tail)

    # Compute loop depth for each block (number of loops it participates in)
    for bb in cfg.blocks:
        bb.loop_depth = sum(1 for loop in loops if bb.block_id in loop.body)

    cfg.loops = loops


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_cfg(instructions: List[TACInstruction]) -> ControlFlowGraph:
    """
    Build a fully-analysed Control Flow Graph from a flat TAC instruction list.

    Pipeline:
      1. Identify leaders → partition into basic blocks
      2. Wire successor/predecessor edges
      3. Compute dominators (iterative Cooper et al.)
      4. Compute dominance frontiers
      5. Detect natural loops

    Returns a ControlFlowGraph with all fields populated.
    """
    if not instructions:
        empty_block = BasicBlock("B0", [], 0, -1)
        empty_block.dominators = frozenset({"B0"})
        return ControlFlowGraph(
            blocks=[empty_block],
            entry_id="B0",
            block_map={"B0": empty_block},
            label_to_block={},
            loops=[],
        )

    leaders, label_indices = _identify_leaders(instructions)
    blocks, index_to_bid = _build_blocks(instructions, leaders)

    label_to_block: Dict[str, str] = {
        label: index_to_bid[idx] for label, idx in label_indices.items()
    }
    block_map: Dict[str, BasicBlock] = {bb.block_id: bb for bb in blocks}

    _connect_edges(blocks, block_map, label_to_block)

    cfg = ControlFlowGraph(
        blocks=blocks,
        entry_id=blocks[0].block_id,
        block_map=block_map,
        label_to_block=label_to_block,
        loops=[],
    )

    _compute_dominators(cfg)
    _compute_dominance_frontiers(cfg)
    _compute_loops(cfg)

    return cfg


# ---------------------------------------------------------------------------
# Visualization — Graphviz DOT export
# ---------------------------------------------------------------------------

def _escape_label(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\l")


def cfg_to_dot(cfg: ControlFlowGraph, program_name: str = "sudarshan_cfg") -> str:
    """
    Export the CFG as a Graphviz DOT string.

    Nodes show the block id, instructions, and loop/dominator info.
    Back edges are rendered with a dashed arrow.
    Loop headers are coloured steel-blue.
    """
    lines: List[str] = [
        f'digraph "{program_name}" {{',
        "  rankdir=TB;",
        "  node [shape=box, fontname=\"Courier\", fontsize=10];",
        "  edge [fontname=\"Helvetica\", fontsize=9];",
        "",
    ]

    # Back-edge pairs for dashed styling
    back_edge_set: Set[Tuple[str, str]] = set()
    for loop in cfg.loops:
        back_edge_set.add((loop.tail, loop.header))

    # Nodes
    for bb in cfg.blocks:
        inst_lines = [_escape_label(str(i)) for i in bb.instructions]
        body_text = "\\l".join(inst_lines) + "\\l"
        label = f"{bb.block_id} [depth={bb.loop_depth}]\\n{body_text}"
        if bb.block_id == cfg.entry_id:
            attr = 'style=filled, fillcolor=lightgreen'
        elif bb.is_loop_header:
            attr = 'style=filled, fillcolor=steelblue, fontcolor=white'
        elif bb.loop_depth > 0:
            attr = 'style=filled, fillcolor=lightyellow'
        else:
            attr = 'style=filled, fillcolor=white'
        lines.append(f'  {bb.block_id} [label="{label}", {attr}];')

    lines.append("")

    # Edges
    for bb in cfg.blocks:
        for succ_bid in bb.successors:
            is_back = (bb.block_id, succ_bid) in back_edge_set
            style = 'style=dashed, color=red' if is_back else ''
            label = ' [label="back-edge", ' + style + ']' if is_back else ''
            lines.append(f"  {bb.block_id} -> {succ_bid}{label};")

    lines.append("}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Textual Summary
# ---------------------------------------------------------------------------

def cfg_summary(cfg: ControlFlowGraph) -> str:
    """
    Return a human-readable textual summary of the CFG with statistics.
    """
    total_insts = sum(len(bb.instructions) for bb in cfg.blocks)
    total_edges = sum(len(bb.successors) for bb in cfg.blocks)
    all_vars = cfg.all_variables()

    lines: List[str] = [
        "=== Control Flow Graph Summary ===",
        f"  Blocks          : {len(cfg.blocks)}",
        f"  Instructions    : {total_insts}",
        f"  Edges           : {total_edges}",
        f"  Distinct names  : {len(all_vars)}",
        f"  Natural loops   : {len(cfg.loops)}",
        "",
    ]

    for bb in cfg.blocks:
        idom_str = bb.immediate_dominator or "(none — entry)"
        df_str = "{" + ", ".join(sorted(bb.dominance_frontier)) + "}" if bb.dominance_frontier else "∅"
        loop_hdr = "  [LOOP HEADER]" if bb.is_loop_header else ""
        lines.append(
            f"  {bb.block_id}{loop_hdr} | depth={bb.loop_depth}"
            f" | idom={idom_str} | DF={df_str}"
            f" | preds={bb.predecessors} | succs={bb.successors}"
        )
        for inst in bb.instructions:
            lines.append(f"      {inst}")

    if cfg.loops:
        lines.append("")
        lines.append("  Natural Loops:")
        for loop in cfg.loops:
            lines.append(
                f"    header={loop.header}, back-edge={loop.tail}→{loop.header}"
                f", body={{{', '.join(sorted(loop.body))}}}"
            )

    return "\n".join(lines)
