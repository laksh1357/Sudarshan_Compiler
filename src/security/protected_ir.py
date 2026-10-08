"""Protected TAC container and deterministic integrity metadata."""

from dataclasses import dataclass
import hashlib
from typing import Dict, List

from tac import TACInstruction
from errors import SecurityIntegrityError

from .policy import SecurityPolicy


def canonical_instruction(instruction: TACInstruction) -> str:
    return repr((instruction.op, instruction.arg1, instruction.arg2, instruction.result))


@dataclass
class ProtectedBlock:
    block_id: str
    instruction_indices: List[int]
    integrity: str
    policy: SecurityPolicy


@dataclass
class ProtectedProgram:
    instructions: List[TACInstruction]
    blocks: List[ProtectedBlock]
    metadata_digest: str

    def verify(self) -> None:
        for block in self.blocks:
            payload = "\n".join(
                canonical_instruction(self.instructions[index])
                for index in block.instruction_indices
            )
            digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if digest != block.integrity:
                raise SecurityIntegrityError(
                    f"Integrity verification failed for block {block.block_id}."
                )
        metadata = "|".join(
            f"{block.block_id}:{block.integrity}:{block.policy.selected_protection_level}"
            for block in self.blocks
        )
        digest = hashlib.sha256(metadata.encode("utf-8")).hexdigest()
        if digest != self.metadata_digest:
            raise SecurityIntegrityError("Protected IR metadata integrity verification failed.")
