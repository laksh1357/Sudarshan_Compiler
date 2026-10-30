"""
Data Flow Analysis Module for Sudarshan Compiler.

Implements two canonical backward and forward data-flow analyses:

  1. Live Variable Analysis (backward, union)
     - Computes LiveIn and LiveOut for every basic block.
     - A variable is live at a point if its current value may be read
       before it is redefined on some control-flow path to a program exit.

  2. Reaching Definitions Analysis (forward, union)
     - Computes ReachIn and ReachOut for every basic block.
     - A definition d: v = … reaches a point p if there is a path from d to p
       on which v is not redefined.

Both analyses use the standard iterative work-list algorithm with bit-set
representations (Python sets of strings for correctness and clarity).

Reference:
  Aho, Lam, Sethi, Ullman, "Compilers: Principles, Techniques, and Tools"
  (Dragon Book) 2nd ed., §9.2 (Live Variables) and §9.2 (Reaching Definitions).
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from tac import TACInstruction
from analysis.cfg_advanced import BasicBlock, ControlFlowGraph, build_cfg


# ---------------------------------------------------------------------------
# Generic result container
# ---------------------------------------------------------------------------

@dataclass
class DataFlowResult:
    """
    Holds the per-block data-flow sets for a single analysis pass.

    Use `live_in`, `live_out` for liveness; `reach_in`, `reach_out` for RD.
    """
    analysis: str                                        # "LiveVariable" or "ReachingDefs"
    live_in: Dict[str, FrozenSet[str]] = field(default_factory=dict)
    live_out: Dict[str, FrozenSet[str]] = field(default_factory=dict)
    reach_in: Dict[str, FrozenSet[Tuple[str, str]]] = field(default_factory=dict)
    reach_out: Dict[str, FrozenSet[Tuple[str, str]]] = field(default_factory=dict)
    iterations: int = 0


# ---------------------------------------------------------------------------
# Helper: compute USE and DEF sets for a basic block
# ---------------------------------------------------------------------------

def _use_def(bb: BasicBlock) -> Tuple[Set[str], Set[str]]:
    """
    Compute (USE, DEF) for a single basic block.

    USE: variables used before being defined in this block (upward-exposed uses).
    DEF: variables defined before being used in this block (downward-exposed defs).

    Only string names count; integer literals are ignored.
    LABEL, JUMP instructions are control-flow only — no data use/def.
    """
    use: Set[str] = set()
    defs: Set[str] = set()

    for inst in bb.instructions:
        # Uses (read operands)
        for operand in (inst.arg1, inst.arg2):
            if isinstance(operand, str) and operand not in defs:
                use.add(operand)
        # Special: JUMP_IF_FALSE and PRINT read arg1
        if inst.op in ("JUMP_IF_FALSE", "PRINT"):
            if isinstance(inst.arg1, str) and inst.arg1 not in defs:
                use.add(inst.arg1)
        # Defs (written result)
        if inst.result is not None and isinstance(inst.result, str):
            if inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT"):
                defs.add(inst.result)

    return use, defs


# ---------------------------------------------------------------------------
# Live Variable Analysis
# ---------------------------------------------------------------------------

class LiveVariableAnalysis:
    """
    Backward data-flow analysis computing LiveIn / LiveOut.

    Equations (per block B):
        LiveOut(B) = ∪ { LiveIn(S) : S ∈ succs(B) }
        LiveIn(B)  = USE(B) ∪ (LiveOut(B) − DEF(B))

    Uses a work-list algorithm for efficiency.
    """

    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        self._use: Dict[str, Set[str]] = {}
        self._def: Dict[str, Set[str]] = {}
        self.live_in: Dict[str, FrozenSet[str]] = {}
        self.live_out: Dict[str, FrozenSet[str]] = {}
        self.iterations = 0

    def analyse(self) -> DataFlowResult:
        """Run the analysis and return a DataFlowResult."""
        # Precompute USE/DEF for each block
        for bb in self.cfg.blocks:
            u, d = _use_def(bb)
            self._use[bb.block_id] = u
            self._def[bb.block_id] = d

        # Initialize all sets to empty
        for bb in self.cfg.blocks:
            self.live_in[bb.block_id] = frozenset()
            self.live_out[bb.block_id] = frozenset()

        # Work-list: process all blocks; iterate until convergence
        worklist: deque[str] = deque(bb.block_id for bb in reversed(self.cfg.blocks))
        in_worklist: Set[str] = set(worklist)

        while worklist:
            self.iterations += 1
            bid = worklist.popleft()
            in_worklist.discard(bid)
            bb = self.cfg.block_map[bid]

            # LiveOut(B) = ∪ LiveIn(S) for each successor S
            new_live_out = frozenset(
                v
                for succ_bid in bb.successors
                for v in self.live_in.get(succ_bid, frozenset())
            )

            # LiveIn(B) = USE(B) ∪ (LiveOut(B) - DEF(B))
            new_live_in = frozenset(
                self._use[bid] | (new_live_out - self._def[bid])
            )

            if (new_live_in != self.live_in[bid] or
                    new_live_out != self.live_out[bid]):
                self.live_in[bid] = new_live_in
                self.live_out[bid] = new_live_out
                # Re-add predecessors to worklist
                for pred_bid in bb.predecessors:
                    if pred_bid not in in_worklist:
                        worklist.append(pred_bid)
                        in_worklist.add(pred_bid)

        return DataFlowResult(
            analysis="LiveVariable",
            live_in=dict(self.live_in),
            live_out=dict(self.live_out),
            iterations=self.iterations,
        )

    def format_report(self) -> str:
        """Return a human-readable report of the liveness results."""
        lines = ["=== Live Variable Analysis ==="]
        for bb in self.cfg.blocks:
            bid = bb.block_id
            lin = sorted(self.live_in.get(bid, frozenset()))
            lout = sorted(self.live_out.get(bid, frozenset()))
            u, d = self._use[bid], self._def[bid]
            lines.append(
                f"  {bid}: USE={sorted(u)} DEF={sorted(d)}"
                f"  |  LiveIn={lin}  LiveOut={lout}"
            )
        lines.append(f"  Converged in {self.iterations} iterations.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reaching Definitions Analysis
# ---------------------------------------------------------------------------

# A definition is identified by (variable_name, block_id) — one per definition
# site in a block (we take the last definition of each var per block for
# accuracy, but track all for completeness).

DefinitionId = Tuple[str, str, int]   # (var_name, block_id, instruction_index)


def _gen_kill(
    bb: BasicBlock,
    all_defs: Dict[str, List[DefinitionId]],
) -> Tuple[FrozenSet[DefinitionId], FrozenSet[DefinitionId]]:
    """
    Compute GEN and KILL for reaching-definitions analysis in block bb.

    GEN:  definitions generated in bb that reach the exit of bb
          (the last definition of each variable defined in bb)
    KILL: all other definitions of the same variables in any block
    """
    # Collect definitions in this block in order
    local_defs: Dict[str, List[DefinitionId]] = defaultdict(list)
    for rel_idx, inst in enumerate(bb.instructions):
        if (inst.result is not None and isinstance(inst.result, str) and
                inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT")):
            def_id: DefinitionId = (str(inst.result), bb.block_id, rel_idx)
            local_defs[str(inst.result)].append(def_id)

    # GEN: last definition of each variable in this block
    gen: Set[DefinitionId] = set()
    for var, dids in local_defs.items():
        gen.add(dids[-1])   # last definition reaches exit

    # KILL: all definitions of the same variable in OTHER blocks (or earlier in same block)
    kill: Set[DefinitionId] = set()
    for var in local_defs:
        for other_did in all_defs.get(var, []):
            if other_did not in gen:
                kill.add(other_did)

    return frozenset(gen), frozenset(kill)


class ReachingDefinitionsAnalysis:
    """
    Forward data-flow analysis computing ReachIn / ReachOut.

    Equations (per block B):
        ReachIn(B)  = ∪ { ReachOut(P) : P ∈ preds(B) }
        ReachOut(B) = GEN(B) ∪ (ReachIn(B) − KILL(B))

    Uses a work-list algorithm.
    """

    def __init__(self, cfg: ControlFlowGraph):
        self.cfg = cfg
        self._gen: Dict[str, FrozenSet[DefinitionId]] = {}
        self._kill: Dict[str, FrozenSet[DefinitionId]] = {}
        self.reach_in: Dict[str, FrozenSet[DefinitionId]] = {}
        self.reach_out: Dict[str, FrozenSet[DefinitionId]] = {}
        self.iterations = 0

    def analyse(self) -> DataFlowResult:
        """Run the analysis and return a DataFlowResult."""
        # Build global all_defs map: var → list of all (var, block, idx) across all blocks
        all_defs: Dict[str, List[DefinitionId]] = defaultdict(list)
        for bb in self.cfg.blocks:
            for rel_idx, inst in enumerate(bb.instructions):
                if (inst.result is not None and isinstance(inst.result, str) and
                        inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT")):
                    all_defs[str(inst.result)].append((str(inst.result), bb.block_id, rel_idx))

        # Precompute GEN/KILL
        for bb in self.cfg.blocks:
            g, k = _gen_kill(bb, all_defs)
            self._gen[bb.block_id] = g
            self._kill[bb.block_id] = k

        # Initialize
        for bb in self.cfg.blocks:
            self.reach_in[bb.block_id] = frozenset()
            self.reach_out[bb.block_id] = self._gen[bb.block_id]

        # Work-list
        worklist: deque[str] = deque(bb.block_id for bb in self.cfg.blocks)
        in_worklist: Set[str] = set(worklist)

        while worklist:
            self.iterations += 1
            bid = worklist.popleft()
            in_worklist.discard(bid)
            bb = self.cfg.block_map[bid]

            # ReachIn(B) = ∪ ReachOut(P) for each predecessor P
            new_reach_in = frozenset(
                d
                for pred_bid in bb.predecessors
                for d in self.reach_out.get(pred_bid, frozenset())
            )

            # ReachOut(B) = GEN(B) ∪ (ReachIn(B) - KILL(B))
            new_reach_out = frozenset(
                self._gen[bid] | (new_reach_in - self._kill[bid])
            )

            if (new_reach_in != self.reach_in[bid] or
                    new_reach_out != self.reach_out[bid]):
                self.reach_in[bid] = new_reach_in
                self.reach_out[bid] = new_reach_out
                for succ_bid in bb.successors:
                    if succ_bid not in in_worklist:
                        worklist.append(succ_bid)
                        in_worklist.add(succ_bid)

        # Convert DefinitionId tuples to string repr for the generic result
        def id_to_str(did: DefinitionId) -> str:
            var, blk, idx = did
            return f"{var}@{blk}[{idx}]"

        rd_in: Dict[str, FrozenSet[str]] = {
            bid: frozenset(id_to_str(d) for d in s)
            for bid, s in self.reach_in.items()
        }
        rd_out: Dict[str, FrozenSet[str]] = {
            bid: frozenset(id_to_str(d) for d in s)
            for bid, s in self.reach_out.items()
        }

        return DataFlowResult(
            analysis="ReachingDefinitions",
            reach_in=rd_in,
            reach_out=rd_out,
            iterations=self.iterations,
        )

    def format_report(self) -> str:
        """Return a human-readable reaching-definitions report."""
        lines = ["=== Reaching Definitions Analysis ==="]
        for bb in self.cfg.blocks:
            bid = bb.block_id
            ri = sorted(f"{v}@{blk}[{i}]" for v, blk, i in self.reach_in.get(bid, frozenset()))
            ro = sorted(f"{v}@{blk}[{i}]" for v, blk, i in self.reach_out.get(bid, frozenset()))
            g = sorted(f"{v}@{blk}[{i}]" for v, blk, i in self._gen.get(bid, frozenset()))
            k = sorted(f"{v}@{blk}[{i}]" for v, blk, i in self._kill.get(bid, frozenset()))
            lines.append(f"  {bid}: GEN={g}  KILL={k}")
            lines.append(f"       ReachIn={ri}")
            lines.append(f"       ReachOut={ro}")
        lines.append(f"  Converged in {self.iterations} iterations.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def liveness_result(instructions: List[TACInstruction]) -> DataFlowResult:
    """Run live variable analysis on a TAC instruction list, return DataFlowResult."""
    cfg = build_cfg(instructions)
    analysis = LiveVariableAnalysis(cfg)
    return analysis.analyse()


def reaching_defs_result(instructions: List[TACInstruction]) -> DataFlowResult:
    """Run reaching definitions analysis on a TAC list, return DataFlowResult."""
    cfg = build_cfg(instructions)
    analysis = ReachingDefinitionsAnalysis(cfg)
    return analysis.analyse()
