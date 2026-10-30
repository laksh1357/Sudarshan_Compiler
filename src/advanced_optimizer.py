"""
Advanced Optimization Engine for Sudarshan Compiler.

Implements five CFG-aware optimization passes:

  1. Common Subexpression Elimination (CSE)
       Replaces repeated computations of the same expression with a copy
       of a previously computed temporary.

  2. Copy Propagation
       Replaces uses of a variable that was defined by a simple copy (t = x)
       with the original source wherever it is still live.

  3. Loop Invariant Code Motion (LICM)
       Identifies computations inside a loop whose operands are never modified
       inside the loop, and hoists them to the loop's pre-header block.

  4. Strength Reduction
       Replaces expensive operations with cheaper equivalents inside loops
       (e.g. multiply-by-induction-variable → repeated addition).

  5. Algebraic Simplification (extended)
       Applies arithmetic identities and strength-reduction rules on
       individual instructions regardless of loop context.

Design principles:
  - Every pass is semantics-preserving and independently testable.
  - Passes compose via the OptimizationPassManager.
  - Before/after TAC comparison is produced for every transformed instruction.
  - Statistics (instruction count delta, pass-level transform count) are emitted.
  - No pass introduces instructions that the Sudarshan VM cannot execute.
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from tac import TACInstruction, dump_tac
from analysis.cfg_advanced import BasicBlock, ControlFlowGraph, build_cfg
from analysis.dataflow import LiveVariableAnalysis


# ---------------------------------------------------------------------------
# Shared data structures
# ---------------------------------------------------------------------------

@dataclass
class OptRecord:
    """One concrete transformation performed by an optimization pass."""
    pass_name: str
    original: str
    transformed: str
    reason: str
    category: str

    def to_dict(self) -> dict:
        return {
            "pass_name": self.pass_name,
            "original": self.original,
            "transformed": self.transformed,
            "reason": self.reason,
            "category": self.category,
        }


@dataclass
class PassStats:
    """Statistics produced by a single optimization pass."""
    pass_name: str
    transforms_applied: int = 0
    instructions_before: int = 0
    instructions_after: int = 0

    @property
    def reduction(self) -> int:
        return self.instructions_before - self.instructions_after


@dataclass
class OptimizationReport:
    """Aggregated results from all passes in the pass manager."""
    records: List[OptRecord] = field(default_factory=list)
    pass_stats: List[PassStats] = field(default_factory=list)
    instructions_before: int = 0
    instructions_after: int = 0
    total_transforms: int = 0

    @property
    def reduction_pct(self) -> float:
        if self.instructions_before == 0:
            return 0.0
        return round(
            (self.instructions_before - self.instructions_after)
            / self.instructions_before * 100, 2
        )

    def summary(self) -> str:
        lines = [
            "=== Advanced Optimization Report ===",
            f"  Instructions before : {self.instructions_before}",
            f"  Instructions after  : {self.instructions_after}",
            f"  Total transforms    : {self.total_transforms}",
            f"  Reduction           : {self.reduction_pct}%",
            "",
        ]
        for ps in self.pass_stats:
            lines.append(
                f"  [{ps.pass_name}] "
                f"transforms={ps.transforms_applied} "
                f"code-size {ps.instructions_before}→{ps.instructions_after}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pass 1: Common Subexpression Elimination (CSE)
# ---------------------------------------------------------------------------

# An expression key: (op, arg1_canonical, arg2_canonical)
# Canonicalize commutative ops (ADD, MUL) so (op, a, b) == (op, b, a).
_COMMUTATIVE = {"ADD", "MUL", "EQ", "NE"}

ExprKey = Tuple[str, Any, Any]


def _canon_key(op: str, a1: Any, a2: Any) -> ExprKey:
    if op in _COMMUTATIVE:
        return (op, *sorted([str(a1), str(a2)]))
    return (op, str(a1) if a1 is not None else None, str(a2) if a2 is not None else None)


def _is_pure_bin_op(op: str) -> bool:
    return op in {"ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT", "LE", "GE", "NEG"}


def cse_pass(
    instructions: List[TACInstruction],
) -> Tuple[List[TACInstruction], List[OptRecord]]:
    """
    Local CSE within each basic block.

    Tracks available expressions (op, arg1, arg2) → result_temp.
    When the same expression is seen again, replaces the computation
    with an ASSIGN from the previously computed temporary.

    Invalidates the available expression map on any instruction that
    redefines an operand (kills expressions involving that operand).
    """
    cfg = build_cfg(instructions)
    records: List[OptRecord] = []

    # Build a mapping from original instruction index to modified instruction
    modified: Dict[int, TACInstruction] = {}

    for bb in cfg.blocks:
        avail: Dict[ExprKey, str] = {}   # expr_key → result name

        for i, inst in enumerate(bb.instructions):
            glob_idx = bb.first_index + i

            if _is_pure_bin_op(inst.op) and inst.result is not None:
                key: ExprKey
                if inst.op == "NEG":
                    key = ("NEG", str(inst.arg1) if inst.arg1 is not None else None, None)
                else:
                    key = _canon_key(inst.op, inst.arg1, inst.arg2)

                if key in avail:
                    prev_result = avail[key]
                    orig_text = str(inst)
                    new_inst = TACInstruction("ASSIGN", prev_result, None, inst.result)
                    modified[glob_idx] = new_inst
                    records.append(OptRecord(
                        pass_name="CSE",
                        original=orig_text,
                        transformed=str(new_inst),
                        reason=f"Expression already computed in '{prev_result}'; replaced with copy",
                        category="cse",
                    ))
                else:
                    avail[key] = str(inst.result)

            # Invalidate available expressions that use the newly-defined result
            if inst.result is not None and isinstance(inst.result, str):
                to_remove = [
                    k for k, v in avail.items()
                    if (k[1] == str(inst.result) or k[2] == str(inst.result))
                    and v != str(inst.result)
                ]
                for k in to_remove:
                    del avail[k]

            # Control-flow boundaries: clear everything
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_FALSE"):
                avail.clear()

    result = [modified.get(i, inst) for i, inst in enumerate(instructions)]
    return result, records


# ---------------------------------------------------------------------------
# Pass 2: Copy Propagation
# ---------------------------------------------------------------------------

def copy_propagation_pass(
    instructions: List[TACInstruction],
) -> Tuple[List[TACInstruction], List[OptRecord]]:
    """
    Local Copy Propagation within each basic block.

    Tracks copy assignments: t = x → propagates x wherever t is used,
    as long as neither t nor x has been redefined in the interim.

    Clears the copy map at control-flow instructions for safety.
    """
    cfg = build_cfg(instructions)
    records: List[OptRecord] = []
    modified: Dict[int, TACInstruction] = {}

    for bb in cfg.blocks:
        copies: Dict[str, str] = {}   # lhs → rhs (from ASSIGN instructions)

        for i, inst in enumerate(bb.instructions):
            glob_idx = bb.first_index + i

            # Clear state on control-flow boundaries
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_FALSE"):
                copies.clear()
                modified[glob_idx] = inst
                continue

            def propagate(val: Any) -> Any:
                if isinstance(val, str):
                    while val in copies:
                        val = copies[val]
                return val

            new_arg1 = propagate(inst.arg1)
            new_arg2 = propagate(inst.arg2)

            changed = (new_arg1 != inst.arg1) or (new_arg2 != inst.arg2)

            if changed:
                orig_text = str(inst)
                new_inst = TACInstruction(inst.op, new_arg1, new_arg2, inst.result)
                modified[glob_idx] = new_inst
                records.append(OptRecord(
                    pass_name="CopyPropagation",
                    original=orig_text,
                    transformed=str(new_inst),
                    reason="Substituted copy source for copy destination operand(s)",
                    category="copy_propagation",
                ))
                inst = new_inst

            # Track new copy definitions
            if inst.op == "ASSIGN" and isinstance(inst.arg1, str) and inst.result is not None:
                copies[str(inst.result)] = str(inst.arg1)
            else:
                # Any redefinition of lhs invalidates copies through it
                if inst.result is not None and isinstance(inst.result, str):
                    copies.pop(str(inst.result), None)
                    # Also invalidate any copies whose rhs was redefined
                    stale = [lhs for lhs, rhs in copies.items() if rhs == str(inst.result)]
                    for lhs in stale:
                        del copies[lhs]

    result = [modified.get(i, inst) for i, inst in enumerate(instructions)]
    return result, records


# ---------------------------------------------------------------------------
# Pass 3: Loop Invariant Code Motion (LICM)
# ---------------------------------------------------------------------------

def _operand_defined_in_loop(
    operand: Any,
    loop_body_bids: Set[str],
    cfg: ControlFlowGraph,
) -> bool:
    """
    Return True if operand (a name) is defined by any instruction inside the loop.
    """
    if not isinstance(operand, str):
        return False   # numeric literal — always loop-invariant
    for bid in loop_body_bids:
        bb = cfg.block_map[bid]
        for inst in bb.instructions:
            if (inst.result is not None and str(inst.result) == operand and
                    inst.op not in ("LABEL", "JUMP", "JUMP_IF_FALSE", "PRINT")):
                return True
    return False


def licm_pass(
    instructions: List[TACInstruction],
) -> Tuple[List[TACInstruction], List[OptRecord]]:
    """
    Loop Invariant Code Motion.

    For each natural loop:
      1. Find the pre-header block (predecessor of the loop header that is
         not itself in the loop). If none exists, skip the loop.
      2. Mark each instruction in the loop as loop-invariant if ALL of its
         operands are either numeric literals or names defined outside the loop.
      3. Hoist the invariant instructions to the pre-header block (in dependency
         order), removing them from their original position in the loop.

    Only pure arithmetic/comparison instructions (no branches, prints, labels)
    are candidates for hoisting.
    """
    cfg = build_cfg(instructions)
    records: List[OptRecord] = []

    # We will rebuild the instruction list from cfg with hoisted instructions inserted
    # Work with a flat index → instruction mapping that we can mutate
    inst_list: List[Optional[TACInstruction]] = list(instructions)

    for loop in cfg.loops:
        header_bid = loop.header
        loop_body = loop.body

        # Find pre-header: a predecessor of the header that is NOT in the loop
        header_bb = cfg.block_map[header_bid]
        pre_header_bids = [p for p in header_bb.predecessors if p not in loop_body]
        if not pre_header_bids:
            continue   # No pre-header, skip
        pre_header_bid = pre_header_bids[0]
        pre_header_bb = cfg.block_map[pre_header_bid]

        # Collect loop-invariant instruction indices (excluding header's phi-like setup)
        invariant_indices: List[int] = []

        for bid in sorted(loop_body):
            bb = cfg.block_map[bid]
            for i, inst in enumerate(bb.instructions):
                glob_idx = bb.first_index + i
                if inst_list[glob_idx] is None:
                    continue
                if inst.op not in {"ADD", "SUB", "MUL", "DIV", "NEG",
                                   "EQ", "NE", "LT", "GT", "LE", "GE",
                                   "CONST", "ASSIGN"}:
                    continue
                if inst.result is None:
                    continue
                # All operands must be loop-invariant
                arg1_invariant = not _operand_defined_in_loop(inst.arg1, loop_body, cfg)
                arg2_invariant = not _operand_defined_in_loop(inst.arg2, loop_body, cfg)
                if arg1_invariant and arg2_invariant:
                    invariant_indices.append(glob_idx)

        if not invariant_indices:
            continue

        # Hoist: collect instructions to move, remove from body
        hoisted: List[TACInstruction] = []
        for glob_idx in invariant_indices:
            hi = inst_list[glob_idx]
            if hi is not None:
                records.append(OptRecord(
                    pass_name="LICM",
                    original=str(hi),
                    transformed=f"[hoisted to {pre_header_bid}] {hi}",
                    reason=f"Instruction is loop-invariant; hoisted from loop body to pre-header {pre_header_bid}",
                    category="licm",
                ))
                hoisted.append(hi)
                inst_list[glob_idx] = None   # Mark as removed from body

        # Insert hoisted instructions before the last instruction of the pre-header
        # (before the branch to the loop header)
        last_pre_header_idx = pre_header_bb.last_index
        # Find the insertion position: just before the last instruction
        insert_pos = last_pre_header_idx
        # Build the new flat list:
        new_list: List[Optional[TACInstruction]] = list(inst_list[:insert_pos])
        new_list.extend(hoisted)
        new_list.extend(inst_list[insert_pos:])
        inst_list = new_list

    # Filter out None (removed instructions) and return
    result = [i for i in inst_list if i is not None]
    return result, records


# ---------------------------------------------------------------------------
# Pass 4: Strength Reduction (inside loops)
# ---------------------------------------------------------------------------

def strength_reduction_pass(
    instructions: List[TACInstruction],
) -> Tuple[List[TACInstruction], List[OptRecord]]:
    """
    Strength Reduction inside loops.

    Applies the following reductions on instructions within loop bodies:
      - Multiplication by a power of 2 → left shift expressed as repeated ADD
        (since the VM only supports +, -, *, /; we lower mul-by-2 to add+add)
      - x * 2 → x + x
      - x * 0 → CONST 0    (also in algebraic pass, kept here for completeness)
      - x ** 2 is not a TAC op, so not applicable

    These are only applied inside loop bodies to maximise benefit.
    """
    cfg = build_cfg(instructions)
    records: List[OptRecord] = []
    modified: Dict[int, TACInstruction] = {}

    loop_insts: Set[int] = set()
    for loop in cfg.loops:
        for bid in loop.body:
            bb = cfg.block_map[bid]
            for i in range(len(bb.instructions)):
                loop_insts.add(bb.first_index + i)

    for glob_idx, inst in enumerate(instructions):
        if glob_idx not in loop_insts:
            continue
        if inst.op == "MUL" and inst.result is not None:
            # x * 2 → x + x  (cheaper on many architectures)
            if inst.arg2 == 2 and isinstance(inst.arg1, str):
                orig_text = str(inst)
                new_inst = TACInstruction("ADD", inst.arg1, inst.arg1, inst.result)
                modified[glob_idx] = new_inst
                records.append(OptRecord(
                    pass_name="StrengthReduction",
                    original=orig_text,
                    transformed=str(new_inst),
                    reason="x * 2 → x + x (strength reduction: mul→add inside loop)",
                    category="strength_reduction",
                ))
            elif inst.arg1 == 2 and isinstance(inst.arg2, str):
                orig_text = str(inst)
                new_inst = TACInstruction("ADD", inst.arg2, inst.arg2, inst.result)
                modified[glob_idx] = new_inst
                records.append(OptRecord(
                    pass_name="StrengthReduction",
                    original=orig_text,
                    transformed=str(new_inst),
                    reason="2 * x → x + x (strength reduction: mul→add inside loop)",
                    category="strength_reduction",
                ))
            # x * 4 → (x + x) + (x + x): create two temporaries
            elif inst.arg2 == 4 and isinstance(inst.arg1, str):
                orig_text = str(inst)
                # We can't introduce new temporaries mid-pass without coordinating naming.
                # Instead, only mark for logging — the algebraic pass handles x*0, x*1.
                # For x*4 we leave the mul (a deeper induction-variable reduction is not
                # implemented here to keep the pass minimal and correct).
                pass

    result = [modified.get(i, inst) for i, inst in enumerate(instructions)]
    return result, records


# ---------------------------------------------------------------------------
# Pass 5: Algebraic Simplification (extended)
# ---------------------------------------------------------------------------

def algebraic_simplification_pass(
    instructions: List[TACInstruction],
) -> Tuple[List[TACInstruction], List[OptRecord]]:
    """
    Applies algebraic identity rules on individual TAC instructions.

    Rules applied:
      x + 0 → x        0 + x → x
      x - 0 → x        x - x → 0
      x * 0 → 0        0 * x → 0
      x * 1 → x        1 * x → x
      x / 1 → x
      x == x → 1       x != x → 0

    This is an extended version of the algebraic simplification in the original
    tac_opt.py, but implemented as a standalone pass so it can be composed via
    the pass manager independently.
    """
    records: List[OptRecord] = []
    result: List[TACInstruction] = []

    for inst in instructions:
        a1, a2, op, res = inst.arg1, inst.arg2, inst.op, inst.result

        def record_and_replace(reason: str, new_inst: TACInstruction) -> TACInstruction:
            records.append(OptRecord(
                pass_name="AlgebraicSimplification",
                original=str(inst),
                transformed=str(new_inst),
                reason=reason,
                category="algebraic",
            ))
            return new_inst

        new: Optional[TACInstruction] = None

        if op == "ADD":
            if a2 == 0:
                new = record_and_replace("x + 0 → x", TACInstruction("ASSIGN", a1, None, res))
            elif a1 == 0:
                new = record_and_replace("0 + x → x", TACInstruction("ASSIGN", a2, None, res))

        elif op == "SUB":
            if a2 == 0:
                new = record_and_replace("x - 0 → x", TACInstruction("ASSIGN", a1, None, res))
            elif isinstance(a1, str) and a1 == str(a2):
                new = record_and_replace("x - x → 0", TACInstruction("CONST", 0, None, res))

        elif op == "MUL":
            if a1 == 0 or a2 == 0:
                new = record_and_replace("x * 0 → 0", TACInstruction("CONST", 0, None, res))
            elif a2 == 1:
                new = record_and_replace("x * 1 → x", TACInstruction("ASSIGN", a1, None, res))
            elif a1 == 1:
                new = record_and_replace("1 * x → x", TACInstruction("ASSIGN", a2, None, res))

        elif op == "DIV":
            if a2 == 1:
                new = record_and_replace("x / 1 → x", TACInstruction("ASSIGN", a1, None, res))

        elif op == "EQ":
            if isinstance(a1, str) and a1 == str(a2):
                new = record_and_replace("x == x → 1", TACInstruction("CONST", 1, None, res))

        elif op == "NE":
            if isinstance(a1, str) and a1 == str(a2):
                new = record_and_replace("x != x → 0", TACInstruction("CONST", 0, None, res))

        result.append(new if new is not None else inst)

    return result, records


# ---------------------------------------------------------------------------
# Optimization Level definitions
# ---------------------------------------------------------------------------

# An optimization level maps to an ordered list of pass functions.
# Each pass function has signature:
#   (List[TACInstruction]) → Tuple[List[TACInstruction], List[OptRecord]]

PassFn = Any   # Callable[[List[TACInstruction]], Tuple[List[TACInstruction], List[OptRecord]]]

OPTIMIZATION_LEVELS: Dict[str, List[PassFn]] = {
    "O0": [],    # No optimization (analysis only)
    "O1": [
        algebraic_simplification_pass,
        copy_propagation_pass,
    ],
    "O2": [
        algebraic_simplification_pass,
        cse_pass,
        copy_propagation_pass,
        algebraic_simplification_pass,   # second sweep after CSE/CP
    ],
    "O3": [
        algebraic_simplification_pass,
        cse_pass,
        copy_propagation_pass,
        licm_pass,
        strength_reduction_pass,
        algebraic_simplification_pass,
        copy_propagation_pass,   # clean up after LICM/SR
        cse_pass,               # final CSE sweep
    ],
}


# ---------------------------------------------------------------------------
# Optimization Pass Manager
# ---------------------------------------------------------------------------

class OptimizationPassManager:
    """
    Manages the execution of optimization passes in a configurable pipeline.

    Usage::

        manager = OptimizationPassManager(level="O2")
        optimized, report = manager.run(instructions)
        print(report.summary())
        print(compare_ir(instructions, optimized))

    Levels:
        O0: No optimization passes run.
        O1: Algebraic simplification + copy propagation.
        O2: O1 + CSE (bi-directional sweep).
        O3: O2 + LICM + strength reduction + additional cleanup sweeps.
    """

    def __init__(self, level: str = "O2", passes: Optional[List[PassFn]] = None):
        """
        Args:
            level:  Optimization level string ("O0"/"O1"/"O2"/"O3").
                    Ignored if `passes` is explicitly provided.
            passes: Optional explicit list of pass functions. Overrides `level`.
        """
        if level not in OPTIMIZATION_LEVELS and passes is None:
            raise ValueError(
                f"Unknown optimization level '{level}'. "
                f"Valid: {sorted(OPTIMIZATION_LEVELS)}"
            )
        self.level = level
        self._passes: List[PassFn] = passes if passes is not None else OPTIMIZATION_LEVELS[level]

    @property
    def pass_names(self) -> List[str]:
        return [fn.__name__ for fn in self._passes]

    def run(
        self, instructions: List[TACInstruction]
    ) -> Tuple[List[TACInstruction], OptimizationReport]:
        """
        Run all configured passes in sequence and return the optimized
        instruction list along with an OptimizationReport.
        """
        report = OptimizationReport(instructions_before=len(instructions))
        current = list(instructions)
        all_records: List[OptRecord] = []

        for pass_fn in self._passes:
            before_count = len(current)
            current, pass_records = pass_fn(current)
            after_count = len(current)
            ps = PassStats(
                pass_name=pass_fn.__name__,
                transforms_applied=len(pass_records),
                instructions_before=before_count,
                instructions_after=after_count,
            )
            report.pass_stats.append(ps)
            all_records.extend(pass_records)

        report.records = all_records
        report.instructions_after = len(current)
        report.total_transforms = len(all_records)
        return current, report


# ---------------------------------------------------------------------------
# Before/After IR comparison utility
# ---------------------------------------------------------------------------

def compare_ir(
    before: List[TACInstruction],
    after: List[TACInstruction],
    title: str = "Optimization Comparison",
) -> str:
    """
    Return a side-by-side (sequential) BEFORE / AFTER comparison string.
    """
    lines = [
        f"=== {title} ===",
        "--- BEFORE ---",
        dump_tac(before),
        "",
        "--- AFTER ---",
        dump_tac(after),
    ]
    return "\n".join(lines)
