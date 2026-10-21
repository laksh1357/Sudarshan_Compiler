"""
Interpreter / Virtual Machine Module for Sudarshan Compiler.

Executes linear Three-Address Code (TAC) instructions sequentially,
maintaining variable memory, temporary memory, label map, and program counter (PC).
Raises CompilerRuntimeError from errors.py for runtime errors such as division by zero.
"""

from typing import Any, Dict, List
from errors import CompilerRuntimeError
from tac import TACInstruction


class Interpreter:
    """
    Virtual Machine that executes TAC quadruples.
    Demonstrates the final execution phase of the compiler pipeline.
    """

    def __init__(self, instructions: List[TACInstruction], max_steps: Optional[int] = None):
        self.instructions = instructions
        self.memory: Dict[str, int] = {}
        self.label_map: Dict[str, int] = {}
        self.output: List[int] = []
        self.pc = 0
        self.step_count = 0
        self.max_steps = max_steps

        # Pre-pass: Index label locations for O(1) GOTO jumps
        for idx, inst in enumerate(self.instructions):
            if inst.op == "LABEL" and inst.result:
                self.label_map[inst.result] = idx

    def _eval_operand(self, operand: Any) -> int:
        """Evaluates an operand which can be an integer literal, variable, or temporary."""
        if operand is None:
            raise CompilerRuntimeError("Attempted to evaluate None operand.")

        if isinstance(operand, int):
            return operand

        if isinstance(operand, str):
            if operand in self.memory:
                return self.memory[operand]
            raise CompilerRuntimeError(f"Undefined variable or temporary '{operand}' accessed before initialization.")

        raise CompilerRuntimeError(f"Invalid operand type '{type(operand).__name__}'.")

    def run(self) -> List[int]:
        """
        Runs the TAC instruction execution loop.
        Returns a list of values printed during execution.
        """
        self.pc = 0
        self.step_count = 0
        n = len(self.instructions)

        while self.pc < n:
            self.step_count += 1
            if self.max_steps is not None and self.step_count > self.max_steps:
                raise CompilerRuntimeError(f"Execution step limit exceeded ({self.max_steps} steps). Potential infinite loop.")

            inst = self.instructions[self.pc]
            op = inst.op

            if op in ("CONST", "ASSIGN"):
                val = self._eval_operand(inst.arg1)
                self.memory[inst.result] = val
                self.pc += 1

            elif op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT", "LE", "GE"):
                val1 = self._eval_operand(inst.arg1)
                val2 = self._eval_operand(inst.arg2)
                res = 0

                if op == "ADD":
                    res = val1 + val2
                elif op == "SUB":
                    res = val1 - val2
                elif op == "MUL":
                    res = val1 * val2
                elif op == "DIV":
                    if val2 == 0:
                        raise CompilerRuntimeError("Division by zero.")
                    res = val1 // val2
                elif op == "EQ":
                    res = 1 if val1 == val2 else 0
                elif op == "NE":
                    res = 1 if val1 != val2 else 0
                elif op == "LT":
                    res = 1 if val1 < val2 else 0
                elif op == "GT":
                    res = 1 if val1 > val2 else 0
                elif op == "LE":
                    res = 1 if val1 <= val2 else 0
                elif op == "GE":
                    res = 1 if val1 >= val2 else 0

                self.memory[inst.result] = res
                self.pc += 1

            elif op == "NEG":
                val = self._eval_operand(inst.arg1)
                self.memory[inst.result] = -val
                self.pc += 1

            elif op == "PRINT":
                val = self._eval_operand(inst.arg1)
                self.output.append(val)
                print(val)
                self.pc += 1

            elif op == "JUMP":
                target_label = inst.result
                if target_label in self.label_map:
                    self.pc = self.label_map[target_label]
                else:
                    raise CompilerRuntimeError(f"Undefined jump label target '{target_label}'.")

            elif op == "JUMP_IF_FALSE":
                cond_val = self._eval_operand(inst.arg1)
                if cond_val == 0:
                    target_label = inst.result
                    if target_label in self.label_map:
                        self.pc = self.label_map[target_label]
                    else:
                        raise CompilerRuntimeError(f"Undefined jump label target '{target_label}'.")
                else:
                    self.pc += 1

            elif op == "LABEL":
                self.pc += 1

            else:
                raise CompilerRuntimeError(f"Invalid instruction '{op}'.")

        return self.output

