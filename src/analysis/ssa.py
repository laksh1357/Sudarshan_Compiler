"""
Static Single Assignment (SSA) Form Module for Sudarshan Compiler.

Transforms a linear TAC instruction list into SSA form by:
  1. Computing the Dominance Frontier (via the advanced CFG module)
  2. Inserting Phi nodes at the correct join points (Cytron et al. 1991)
  3. Renaming every variable definition to a versioned SSA name (var.0, var.1, …)

References:
  - Cytron, Ferrante, Rosen, Wegman, Zadeck (1991),
    "Efficiently Computing Static Single Assignment Form and the
     Control Dependence Graph", ACM TOPLAS 13(4).

Design principles:
  - Preserves TAC semantics exactly (verified by round-trip tests)
  - Works exclusively from TACInstruction objects; does NOT modify them
  - Back-patching produces fresh TACInstruction objects only
  - Provides ssa_to_tac() to lower SSA back to conventional TAC for the VM
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from tac import TACInstruction
from analysis.cfg_advanced import BasicBlock, ControlFlowGraph, build_cfg


# ---------------------------------------------------------------------------
# SSA-specific data structures
# ---------------------------------------------------------------------------

@dataclass
class SSAVariable:
    """A versioned SSA name: original name + version counter."""
    base: str          # Original variable name (e.g. "x")
    version: int       # Monotonically increasing version (0, 1, 2, …)

    @property
    def name(self) -> str:
        return f"{self.base}.{self.version}"

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, SSAVariable) and self.name == other.name


@dataclass
class PhiNode:
    """
    A Phi (φ) node at the top of a join block.

    phi_result ← φ(v_pred1, v_pred2, …)

    Attributes:
        result:      The SSA name written by this phi (e.g. "x.2")
        args:        Dict mapping predecessor block_id → SSA name of incoming value
        orig_var:    Original variable name (base, pre-SSA)
    """
    result: str                          # SSA name of the defined value
    args: Dict[str, str]                 # pred_bid → ssa_name
    orig_var: str                        # Pre-SSA base name

    def to_tac(self) -> TACInstruction:
        """Lower the phi to a TAC PHI pseudo-instruction for display."""
        args_str = ", ".join(f"{bid}:{v}" for bid, v in sorted(self.args.items()))
        return TACInstruction("PHI", args_str, None, self.result)

    def __str__(self) -> str:
        args_str = ", ".join(f"({bid}){v}" for bid, v in sorted(self.args.items()))
        return f"{self.result} = φ({args_str})"


@dataclass
class SSAInstruction:
    """
    A TAC instruction with SSA-renamed operands and result.

    Wraps a (possibly mutated) TACInstruction but keeps originals separate.
    """
    op: str
    arg1: Any       # SSA name (str) or numeric literal (int/float) or None
    arg2: Any
    result: Any

    def to_tac(self) -> TACInstruction:
        return TACInstruction(self.op, self.arg1, self.arg2, self.result)

    def __str__(self) -> str:
        return str(self.to_tac())


@dataclass
class SSABlock:
    """An SSA-annotated basic block."""
    block_id: str
    phi_nodes: List[PhiNode]             # Phi nodes at the top of the block
    instructions: List[SSAInstruction]   # SSA-renamed body instructions

    def all_instructions_tac(self) -> List[TACInstruction]:
        """Return all instructions (phi nodes first) as TACInstruction objects."""
        result: List[TACInstruction] = [p.to_tac() for p in self.phi_nodes]
        result.extend(i.to_tac() for i in self.instructions)
        return result


@dataclass
class SSAProgram:
    """
    The complete SSA-form program.

    Attributes:
        cfg:     The underlying CFG (with dominator/DF info)
        blocks:  SSA-annotated blocks in program order
    """
    cfg: ControlFlowGraph
    blocks: List[SSABlock]
    block_map: Dict[str, SSABlock] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.block_map = {b.block_id: b for b in self.blocks}

    def to_tac(self) -> List[TACInstruction]:
        """
        Lower the SSA program back to a linear TAC list.
        Phi nodes are converted to PHI pseudo-instructions for display.
        """
        result: List[TACInstruction] = []
        for ssa_block in self.blocks:
            # Emit a LABEL for every block except the entry
            bb = self.cfg.block_map[ssa_block.block_id]
            # If the first instruction of the original block is already a LABEL, keep it
            if bb.instructions and bb.instructions[0].op == "LABEL":
                result.append(bb.instructions[0])  # original label
                for phi in ssa_block.phi_nodes:
                    result.append(phi.to_tac())
                for ssa_inst in ssa_block.instructions[1:]:   # skip the already-added label
                    result.append(ssa_inst.to_tac())
            else:
                for phi in ssa_block.phi_nodes:
                    result.append(phi.to_tac())
                for ssa_inst in ssa_block.instructions:
                    result.append(ssa_inst.to_tac())
        return result


# ---------------------------------------------------------------------------
# Helper: collect all "original" variable names (non-temps that are user vars)
# ---------------------------------------------------------------------------

def _all_defined_names(instructions: List[TACInstruction]) -> Set[str]:
    """
    Return every name that appears as result in any non-branch/label instruction.
    Filters out label names.
    """
    names: Set[str] = set()
    for inst in instructions:
        if inst.result is not None and inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT"):
            names.add(str(inst.result))
    return names


# ---------------------------------------------------------------------------
# Phase 1: Phi-node Insertion (Cytron et al. DF+ criterion)
# ---------------------------------------------------------------------------

def _insert_phi_nodes(
    cfg: ControlFlowGraph,
    defs: Dict[str, Set[str]],   # variable → set of block_ids that define it
) -> Dict[str, List[str]]:
    """
    For each variable v, insert a phi node at each block in DF+(defs(v)).

    Uses the iterative DF+ algorithm:
      worklist ← blocks that define v
      while worklist:
          b ← pop
          for y in DF(b):
              if phi not already at y for v:
                  insert phi at y
                  worklist ← y (if not already processed)

    Returns:
        phi_placement: variable → list of block_ids where phi was placed.
    """
    phi_placement: Dict[str, List[str]] = defaultdict(list)

    for var, def_blocks in defs.items():
        # Semi-pruned SSA: variables defined in at most one block cannot require φ-nodes
        if len(def_blocks) <= 1:
            continue
        worklist: List[str] = list(def_blocks)
        has_phi: Set[str] = set()   # block_ids where phi for var already placed

        while worklist:
            bid = worklist.pop()
            bb = cfg.block_map[bid]
            for frontier_bid in sorted(bb.dominance_frontier):
                if frontier_bid not in has_phi:
                    has_phi.add(frontier_bid)
                    phi_placement[var].append(frontier_bid)
                    # The phi itself counts as a new definition of var
                    if frontier_bid not in def_blocks:
                        worklist.append(frontier_bid)

    return phi_placement


# ---------------------------------------------------------------------------
# Phase 2: Variable Renaming (dominator-tree DFS)
# ---------------------------------------------------------------------------

class _Renamer:
    """
    Renames every use/definition of each variable in SSA form using a
    stack-based renaming walk over the dominator tree.
    """

    def __init__(
        self,
        cfg: ControlFlowGraph,
        phi_placement: Dict[str, List[str]],
    ):
        self.cfg = cfg
        self.phi_placement = phi_placement
        # version counters: var → next version number to assign
        self.counters: Dict[str, int] = defaultdict(int)
        # stacks: var → stack of current SSA version numbers
        self.stacks: Dict[str, List[int]] = defaultdict(list)
        # output: block_id → SSABlock (with phi nodes and renamed instructions)
        self.ssa_blocks: Dict[str, SSABlock] = {}

        # Seed entry stack with version 0 for all variables
        # (This handles variables that might be read before being defined in
        #  unreachable paths — produces a valid but undefined name like x.0)

    def _new_version(self, var: str) -> int:
        v = self.counters[var]
        self.counters[var] += 1
        self.stacks[var].append(v)
        return v

    def _current_version(self, var: str) -> str:
        if self.stacks[var]:
            return f"{var}.{self.stacks[var][-1]}"
        # Variable used before definition (semantic error caught earlier);
        # return version 0 as a safe fallback for analysis purposes.
        return f"{var}.0"

    def _rename_operand(self, operand: Any) -> Any:
        if isinstance(operand, str) and not operand.startswith("L"):
            return self._current_version(operand)
        return operand

    def rename(self) -> None:
        """Start the dominator-tree DFS renaming walk from the entry block."""
        self._rename_block(self.cfg.entry_id, push_counts=[])

    def _rename_block(self, bid: str, push_counts: List[Tuple[str, int]]) -> None:
        """
        Rename one basic block, then recurse into its children in the dominator tree.
        """
        bb = self.cfg.block_map[bid]
        local_push: List[Tuple[str, int]] = []   # (var, stack_depth_before) for popping later

        # ------------------------------------------------------------------
        # Step 1: Initialise phi node definitions for this block
        # ------------------------------------------------------------------
        phi_nodes: List[PhiNode] = []
        if bid in {ph_bid for var, bids in self.phi_placement.items() for ph_bid in bids}:
            # Find all vars that have phis here
            vars_with_phi = [var for var, bids in self.phi_placement.items() if bid in bids]
            for var in sorted(vars_with_phi):
                v = self._new_version(var)
                local_push.append((var, v))
                phi_nodes.append(PhiNode(
                    result=f"{var}.{v}",
                    args={},            # to be back-patched below
                    orig_var=var,
                ))

        # ------------------------------------------------------------------
        # Step 2: Rename body instructions
        # ------------------------------------------------------------------
        ssa_instructions: List[SSAInstruction] = []
        for inst in bb.instructions:
            if inst.op in ("LABEL",):
                # LABEL pseudo-instructions pass through unchanged
                ssa_instructions.append(SSAInstruction(inst.op, inst.arg1, inst.arg2, inst.result))
                continue

            if inst.op in ("JUMP",):
                ssa_instructions.append(SSAInstruction(inst.op, inst.arg1, inst.arg2, inst.result))
                continue

            if inst.op == "JUMP_IF_FALSE":
                new_arg1 = self._rename_operand(inst.arg1)
                ssa_instructions.append(SSAInstruction(inst.op, new_arg1, inst.arg2, inst.result))
                continue

            if inst.op == "PRINT":
                new_arg1 = self._rename_operand(inst.arg1)
                ssa_instructions.append(SSAInstruction(inst.op, new_arg1, inst.arg2, inst.result))
                continue

            # Generic: rename uses first, then rename the definition
            new_arg1 = self._rename_operand(inst.arg1)
            new_arg2 = self._rename_operand(inst.arg2)

            if inst.result is not None and isinstance(inst.result, str):
                v = self._new_version(str(inst.result))
                local_push.append((str(inst.result), v))
                new_result = f"{inst.result}.{v}"
            else:
                new_result = inst.result

            ssa_instructions.append(SSAInstruction(inst.op, new_arg1, new_arg2, new_result))

        # ------------------------------------------------------------------
        # Step 3: Back-patch phi args in successors
        # ------------------------------------------------------------------
        for succ_bid in bb.successors:
            if succ_bid in self.ssa_blocks:
                # The successor was already processed; fill in phi args
                for phi in self.ssa_blocks[succ_bid].phi_nodes:
                    phi.args[bid] = self._current_version(phi.orig_var)

        # ------------------------------------------------------------------
        # Step 4: Store completed SSABlock
        # ------------------------------------------------------------------
        self.ssa_blocks[bid] = SSABlock(bid, phi_nodes, ssa_instructions)

        # ------------------------------------------------------------------
        # Step 5: Recurse into dominator-tree children (blocks idom'd by bid)
        # ------------------------------------------------------------------
        children = sorted(
            b.block_id
            for b in self.cfg.blocks
            if b.immediate_dominator == bid and b.block_id != bid
        )
        for child_bid in children:
            self._rename_block(child_bid, local_push)

        # ------------------------------------------------------------------
        # Step 6: Back-patch phis in successors AFTER children (for backedges)
        # ------------------------------------------------------------------
        for succ_bid in bb.successors:
            if succ_bid not in self.ssa_blocks:
                continue
            for phi in self.ssa_blocks[succ_bid].phi_nodes:
                if bid not in phi.args:
                    phi.args[bid] = self._current_version(phi.orig_var)

        # ------------------------------------------------------------------
        # Step 7: Pop versions pushed in this block
        # ------------------------------------------------------------------
        # Pop in reverse push order to maintain stack discipline
        for var, _ in reversed(local_push):
            if self.stacks[var]:
                self.stacks[var].pop()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_ssa(instructions: List[TACInstruction]) -> SSAProgram:
    """
    Transform a list of TAC instructions into SSA form.

    Steps:
      1. Build CFG (with dominator/DF analysis)
      2. Collect per-block definitions for every variable
      3. Insert Phi nodes at dominance frontiers (Cytron criterion)
      4. Rename every variable to a unique versioned SSA name

    Returns:
        An SSAProgram with all SSABlock objects properly populated.
    """
    cfg = build_cfg(instructions)

    # Collect definition sites per variable
    all_vars = _all_defined_names(instructions)
    defs: Dict[str, Set[str]] = {var: set() for var in all_vars}
    for bb in cfg.blocks:
        for inst in bb.instructions:
            if inst.result is not None and str(inst.result) in all_vars:
                defs[str(inst.result)].add(bb.block_id)

    # Phase 1: insert phi nodes
    phi_placement = _insert_phi_nodes(cfg, defs)

    # Phase 2: rename
    renamer = _Renamer(cfg, phi_placement)
    renamer.rename()

    # Collect SSA blocks in program order (fill in missing blocks with identity)
    ssa_block_list: List[SSABlock] = []
    for bb in cfg.blocks:
        if bb.block_id in renamer.ssa_blocks:
            ssa_block = renamer.ssa_blocks[bb.block_id]
        else:
            # Block never visited (unreachable): keep as-is
            ssa_block = SSABlock(
                bb.block_id,
                phi_nodes=[],
                instructions=[
                    SSAInstruction(i.op, i.arg1, i.arg2, i.result)
                    for i in bb.instructions
                ],
            )
        ssa_block_list.append(ssa_block)

    return SSAProgram(cfg=cfg, blocks=ssa_block_list)


def _strip_version(name: Any) -> Any:
    """
    Strip the SSA version suffix from a name.
    'x.0' → 'x', 't1.2' → 't1'.
    Names without a version suffix or non-string operands pass through unchanged.
    Label names (Lx) never get versioned; pass them through too.
    """
    if not isinstance(name, str):
        return name
    if "." in name:
        base, _, ver = name.rpartition(".")
        if ver.isdigit():
            return base
    return name


def ssa_to_tac(ssa: SSAProgram) -> List[TACInstruction]:
    """
    Lower an SSA program back to conventional (non-SSA) TAC that the
    original Sudarshan VM can execute.

    Steps:
      1. Resolve Phi nodes: for each phi (result ← φ(pred→src, ...)),
         insert ASSIGN(src, result) at the end of each predecessor block,
         before the terminating branch.
      2. De-version all operands and results: map every versioned SSA name
         (e.g. 'x.2', 't1.0') back to its base name ('x', 't1') so that
         the original VM memory model works correctly.
    """
    copies: Dict[str, List[TACInstruction]] = defaultdict(list)

    for ssa_block in ssa.blocks:
        for phi in ssa_block.phi_nodes:
            for pred_bid, src_name in phi.args.items():
                src_val = _strip_version(src_name)
                dst_val = _strip_version(phi.result)
                if src_val != dst_val:
                    copies[pred_bid].append(
                        TACInstruction(
                            "ASSIGN",
                            src_val,
                            None,
                            dst_val,
                        )
                    )

    def deversion_inst(inst: TACInstruction) -> TACInstruction:
        """Return a new TACInstruction with all SSA version suffixes stripped."""
        return TACInstruction(
            inst.op,
            _strip_version(inst.arg1),
            _strip_version(inst.arg2),
            _strip_version(inst.result),
        )

    result: List[TACInstruction] = []
    for ssa_block in ssa.blocks:
        non_phi_insts = [deversion_inst(i.to_tac()) for i in ssa_block.instructions]
        block_copies = [deversion_inst(c) for c in copies.get(ssa_block.block_id, [])]

        if block_copies and non_phi_insts:
            last = non_phi_insts[-1]
            if last.op in ("JUMP", "JUMP_IF_FALSE"):
                result.extend(non_phi_insts[:-1])
                result.extend(block_copies)
                result.append(last)
            else:
                result.extend(non_phi_insts)
                result.extend(block_copies)
        else:
            result.extend(non_phi_insts)

    return result
