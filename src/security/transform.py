"""Transformation framework and protected IR construction."""

import hashlib
from dataclasses import dataclass
from typing import List, Protocol

from tac import TACInstruction

from .config import SecurityConfig
from .cfg import build_cfg
from .policy import SecurityPolicy
from .protected_ir import ProtectedBlock, ProtectedProgram, canonical_instruction


@dataclass(frozen=True)
class SecurityContext:
    """Deterministic context available to future transformations."""

    transformation_version: str = "security-v1"
    compilation_id: str = "default"
    config: SecurityConfig = SecurityConfig()


@dataclass(frozen=True)
class TransformationDiagnostics:
    transformed: bool
    message: str


class SecurityTransformation(Protocol):
    """Interface implemented by semantics-preserving IR transformations."""

    def transform(
        self,
        instructions: List[TACInstruction],
        context: SecurityContext,
    ) -> tuple[List[TACInstruction], TransformationDiagnostics]:
        ...


class IdentityTransformation:
    """Initial transformation implementation; preserves TAC exactly."""

    def transform(
        self,
        instructions: List[TACInstruction],
        context: SecurityContext,
    ) -> tuple[List[TACInstruction], TransformationDiagnostics]:
        return instructions, TransformationDiagnostics(
            transformed=False,
            message="identity transformation; no obfuscation applied",
        )


def protect_ir(
    instructions: List[TACInstruction],
    policies: List[SecurityPolicy],
    context: SecurityContext | None = None,
    transformation: SecurityTransformation | None = None,
) -> ProtectedProgram:
    """Create protected IR and integrity metadata."""
    context = context or SecurityContext()
    transformation = transformation or IdentityTransformation()
    instructions, _ = transformation.transform(instructions, context)
    cfg = build_cfg(instructions)
    policy_map = {policy.block_id: policy for policy in policies}
    blocks: List[ProtectedBlock] = []
    for block in cfg.blocks:
        payload = "\n".join(canonical_instruction(i) for i in block.instructions)
        integrity = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        policy = policy_map[block.block_id]
        blocks.append(ProtectedBlock(block.block_id, block.instruction_indices, integrity, policy))
    metadata = "|".join(
        f"{block.block_id}:{block.integrity}:{block.policy.selected_protection_level}"
        for block in blocks
    )
    metadata_digest = hashlib.sha256(metadata.encode("utf-8")).hexdigest()
    return ProtectedProgram(instructions, blocks, metadata_digest)
