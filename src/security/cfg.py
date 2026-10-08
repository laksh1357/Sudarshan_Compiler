"""Control-flow graph construction for optimized Sudarshan TAC."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from tac import TACInstruction


@dataclass
class BasicBlock:
    """A maximal straight-line TAC region."""

    block_id: str
    instruction_indices: List[int]
    instructions: List[TACInstruction]
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    loop_participation: bool = False


@dataclass
class ControlFlowGraph:
    """Derived CFG for a linear TAC instruction sequence."""

    blocks: List[BasicBlock]
    entry_block: str
    label_to_block: Dict[str, str]

    def block(self, block_id: str) -> BasicBlock:
        return next(block for block in self.blocks if block.block_id == block_id)


def build_cfg(instructions: List[TACInstruction]) -> ControlFlowGraph:
    """Build a deterministic CFG from labels and explicit TAC branches."""
    if not instructions:
        return ControlFlowGraph([], "", {})

    leaders = {0}
    label_indices: Dict[str, int] = {}
    for index, instruction in enumerate(instructions):
        if instruction.op == "LABEL" and instruction.result:
            label_indices[str(instruction.result)] = index
            leaders.add(index)
        if instruction.op in ("JUMP", "JUMP_IF_FALSE"):
            if index + 1 < len(instructions):
                leaders.add(index + 1)
            if instruction.result in label_indices:
                leaders.add(label_indices[instruction.result])

    for instruction in instructions:
        if instruction.op in ("JUMP", "JUMP_IF_FALSE") and instruction.result:
            target_index = label_indices.get(str(instruction.result))
            if target_index is not None:
                leaders.add(target_index)

    ordered_leaders = sorted(leaders)
    blocks: List[BasicBlock] = []
    index_to_block: Dict[int, str] = {}
    for position, start in enumerate(ordered_leaders):
        end = ordered_leaders[position + 1] if position + 1 < len(ordered_leaders) else len(instructions)
        indices = list(range(start, end))
        block = BasicBlock(f"B{position}", indices, [instructions[i] for i in indices])
        blocks.append(block)
        for index in indices:
            index_to_block[index] = block.block_id

    label_to_block = {
        label: index_to_block[index] for label, index in label_indices.items()
    }
    for position, block in enumerate(blocks):
        last = block.instructions[-1]
        if last.op == "JUMP":
            target = label_to_block.get(str(last.result))
            if target:
                block.successors.add(target)
        elif last.op == "JUMP_IF_FALSE":
            target = label_to_block.get(str(last.result))
            if target:
                block.successors.add(target)
            if position + 1 < len(blocks):
                block.successors.add(blocks[position + 1].block_id)
        elif position + 1 < len(blocks):
            block.successors.add(blocks[position + 1].block_id)

    block_map = {block.block_id: block for block in blocks}
    for block in blocks:
        for successor in block.successors:
            block_map[successor].predecessors.add(block.block_id)

    for block in blocks:
        if any(
            successor in block_map
            and blocks.index(block_map[successor]) <= blocks.index(block)
            for successor in block.successors
        ):
            block.loop_participation = True

    return ControlFlowGraph(blocks, blocks[0].block_id, label_to_block)
