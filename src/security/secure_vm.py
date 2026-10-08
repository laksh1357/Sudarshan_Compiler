"""Verified secure execution wrapper around the existing interpreter."""

from typing import List

from errors import SecurityIntegrityError
from interpreter import Interpreter

from .protected_ir import ProtectedProgram


class SecureInterpreter:
    """Verify protected IR, then reuse the existing interpreter semantics."""

    def __init__(self, program: ProtectedProgram):
        self.program = program

    def run(self) -> List[int]:
        self.program.verify()
        labels = {
            instruction.result
            for instruction in self.program.instructions
            if instruction.op == "LABEL" and instruction.result
        }
        for instruction in self.program.instructions:
            if instruction.op in ("JUMP", "JUMP_IF_FALSE") and instruction.result not in labels:
                raise SecurityIntegrityError(
                    f"Invalid protected branch target '{instruction.result}'."
                )
        return Interpreter(self.program.instructions).run()
