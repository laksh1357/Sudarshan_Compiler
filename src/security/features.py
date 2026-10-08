"""Deterministic per-basic-block security feature extraction."""

from dataclasses import dataclass
from typing import Any

from .cfg import BasicBlock


ARITHMETIC_OPS = {"ADD", "SUB", "MUL", "DIV", "NEG"}
COMPARISON_OPS = {"EQ", "NE", "LT", "GT", "LE", "GE"}
BRANCH_OPS = {"JUMP", "JUMP_IF_FALSE"}


@dataclass(frozen=True)
class SecurityFeatures:
    block_id: str
    instruction_count: int
    branch_count: int
    arithmetic_operation_count: int
    comparison_count: int
    constant_count: int
    jump_count: int
    successor_count: int
    predecessor_count: int
    loop_participation: bool
    control_flow_complexity: float
    operand_sensitivity: float


def analyze_block(block: BasicBlock) -> SecurityFeatures:
    """Extract normalized, deterministic features from one basic block."""
    instruction_count = len(block.instructions)
    branch_count = sum(i.op in BRANCH_OPS for i in block.instructions)
    arithmetic_count = sum(i.op in ARITHMETIC_OPS for i in block.instructions)
    comparison_count = sum(i.op in COMPARISON_OPS for i in block.instructions)
    constant_count = sum(i.op == "CONST" for i in block.instructions)
    jump_count = sum(i.op in BRANCH_OPS for i in block.instructions)
    denominator = max(instruction_count, 1)
    complexity = max(
        0.0,
        min(
            1.0,
            (branch_count + comparison_count + len(block.successors) - 1)
            / denominator,
        ),
    )
    sensitive_operands = sum(
        operand is not None and not isinstance(operand, int)
        for instruction in block.instructions
        for operand in (instruction.arg1, instruction.arg2, instruction.result)
    )
    operand_sensitivity = min(1.0, sensitive_operands / max(instruction_count * 3, 1))
    return SecurityFeatures(
        block.block_id,
        instruction_count,
        branch_count,
        arithmetic_count,
        comparison_count,
        constant_count,
        jump_count,
        len(block.successors),
        len(block.predecessors),
        block.loop_participation,
        round(complexity, 6),
        round(operand_sensitivity, 6),
    )
