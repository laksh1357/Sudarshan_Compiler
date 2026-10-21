"""
Three-Address Code (TAC) Optimizer Module for Sudarshan Compiler.

Implements optimization passes over linear TAC instructions:
1. Constant Folding (evaluating constant expressions at compile time)
2. Constant Propagation (substituting known constant values into variables)
3. Dead Code Elimination (removing unreachable instructions after unconditional GOTOs)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
from tac import TACInstruction, dump_tac


@dataclass
class OptimizationRecord:
    """Represents a concrete intermediate code transformation performed by the optimizer."""
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


class TACOptimizer:
    """
    Performs deterministic optimization passes on TAC instructions.
    """

    def __init__(self, instructions: List[TACInstruction]):
        self.instructions = instructions
        self.report: List[OptimizationRecord] = []

    def optimize(self) -> List[TACInstruction]:
        """Runs optimization passes iteratively until no further instructions change."""
        opt_insts, _ = self.optimize_with_report()
        return opt_insts

    def optimize_with_report(self) -> Tuple[List[TACInstruction], List[OptimizationRecord]]:
        """
        Runs optimization passes iteratively until convergence,
        collecting structured reports for each transformation.
        """
        current_insts = self.instructions
        self.report = []

        while True:
            folded_insts = self._constant_folding_and_propagation(current_insts)
            dce_insts = self._dead_code_elimination(folded_insts)
            if len(dce_insts) == len(current_insts) and all(
                i1.op == i2.op and i1.arg1 == i2.arg1 and i1.arg2 == i2.arg2 and i1.result == i2.result
                for i1, i2 in zip(dce_insts, current_insts)
            ):
                break
            current_insts = dce_insts
        return current_insts, self.report

    def _constant_folding_and_propagation(self, insts: List[TACInstruction]) -> List[TACInstruction]:
        """Performs Constant Propagation and Constant Folding."""
        res: List[TACInstruction] = []
        constants: Dict[str, Any] = {}

        for inst in insts:
            # Clear known constant map across control flow boundaries (labels, jumps) for safety
            if inst.op in ("LABEL", "JUMP", "JUMP_IF_FALSE"):
                constants.clear()
                res.append(inst)
                continue

            # Substitute known constants into arg1 and arg2 (Propagation)
            old_arg1 = inst.arg1
            old_arg2 = inst.arg2
            arg1 = constants.get(inst.arg1, inst.arg1) if isinstance(inst.arg1, str) else inst.arg1
            arg2 = constants.get(inst.arg2, inst.arg2) if isinstance(inst.arg2, str) else inst.arg2

            if (arg1 != old_arg1 and isinstance(old_arg1, str)) or (arg2 != old_arg2 and isinstance(old_arg2, str)):
                sub_inst = TACInstruction(inst.op, arg1, arg2, inst.result)
                self.report.append(OptimizationRecord(
                    pass_name="Constant Propagation",
                    original=str(inst),
                    transformed=str(sub_inst),
                    reason=f"Substituted known constant value into instruction",
                    category="constant_propagation"
                ))

            # 1. Full Numeric Constant Folding (when both operands are numbers)
            if inst.op in ("ADD", "SUB", "MUL", "DIV", "EQ", "NE", "LT", "GT", "LE", "GE"):
                if isinstance(arg1, (int, float)) and isinstance(arg2, (int, float)):
                    folded_val: Any = None
                    try:
                        if inst.op == "ADD":
                            folded_val = arg1 + arg2
                        elif inst.op == "SUB":
                            folded_val = arg1 - arg2
                        elif inst.op == "MUL":
                            folded_val = arg1 * arg2
                        elif inst.op == "DIV":
                            if arg2 != 0:
                                folded_val = int(arg1 // arg2) if isinstance(arg1, int) and isinstance(arg2, int) else arg1 / arg2
                        elif inst.op == "EQ":
                            folded_val = 1 if arg1 == arg2 else 0
                        elif inst.op == "NE":
                            folded_val = 1 if arg1 != arg2 else 0
                        elif inst.op == "LT":
                            folded_val = 1 if arg1 < arg2 else 0
                        elif inst.op == "GT":
                            folded_val = 1 if arg1 > arg2 else 0
                        elif inst.op == "LE":
                            folded_val = 1 if arg1 <= arg2 else 0
                        elif inst.op == "GE":
                            folded_val = 1 if arg1 >= arg2 else 0
                    except ZeroDivisionError:
                        folded_val = None

                    if folded_val is not None:
                        new_inst = TACInstruction("CONST", folded_val, None, inst.result)
                        self.report.append(OptimizationRecord(
                            pass_name="Constant Folding",
                            original=f"{inst.result} = {arg1} {inst.op} {arg2}",
                            transformed=f"{inst.result} = {folded_val}",
                            reason=f"Folded constant expression {arg1} {inst.op} {arg2} -> {folded_val}",
                            category="constant_folding"
                        ))
                        res.append(new_inst)
                        if inst.result:
                            constants[inst.result] = folded_val
                        continue

            # 2. Algebraic & Identity Simplifications (when one operand is an identity constant or operands are identical)
            if inst.op == "ADD":
                if arg1 == 0:  # 0 + x -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = 0 ADD {arg2}",
                        transformed=f"{inst.result} = {arg2}",
                        reason="Additive identity: 0 + x = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg2, None, inst.result))
                    continue
                elif arg2 == 0:  # x + 0 -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} ADD 0",
                        transformed=f"{inst.result} = {arg1}",
                        reason="Additive identity: x + 0 = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg1, None, inst.result))
                    continue

            elif inst.op == "SUB":
                if arg2 == 0:  # x - 0 -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} SUB 0",
                        transformed=f"{inst.result} = {arg1}",
                        reason="Subtractive identity: x - 0 = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg1, None, inst.result))
                    continue
                elif arg1 == arg2 and isinstance(arg1, str):  # x - x -> 0
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} SUB {arg2}",
                        transformed=f"{inst.result} = 0",
                        reason="Self-subtraction identity: x - x = 0",
                        category="algebraic"
                    ))
                    new_inst = TACInstruction("CONST", 0, None, inst.result)
                    res.append(new_inst)
                    if inst.result:
                        constants[inst.result] = 0
                    continue

            elif inst.op == "MUL":
                if arg1 == 1:  # 1 * x -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = 1 MUL {arg2}",
                        transformed=f"{inst.result} = {arg2}",
                        reason="Multiplicative identity: 1 * x = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg2, None, inst.result))
                    continue
                elif arg2 == 1:  # x * 1 -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} MUL 1",
                        transformed=f"{inst.result} = {arg1}",
                        reason="Multiplicative identity: x * 1 = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg1, None, inst.result))
                    continue
                elif arg1 == 0 or arg2 == 0:  # x * 0 or 0 * x -> 0
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} MUL {arg2}",
                        transformed=f"{inst.result} = 0",
                        reason="Zero product identity: x * 0 = 0",
                        category="algebraic"
                    ))
                    new_inst = TACInstruction("CONST", 0, None, inst.result)
                    res.append(new_inst)
                    if inst.result:
                        constants[inst.result] = 0
                    continue

            elif inst.op == "DIV":
                if arg2 == 1:  # x / 1 -> x
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} DIV 1",
                        transformed=f"{inst.result} = {arg1}",
                        reason="Division identity: x / 1 = x",
                        category="algebraic"
                    ))
                    res.append(TACInstruction("ASSIGN", arg1, None, inst.result))
                    continue
                elif arg1 == 0 and arg2 != 0:  # 0 / x (where x != 0) -> 0
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = 0 DIV {arg2}",
                        transformed=f"{inst.result} = 0",
                        reason="Zero numerator identity: 0 / x = 0",
                        category="algebraic"
                    ))
                    new_inst = TACInstruction("CONST", 0, None, inst.result)
                    res.append(new_inst)
                    if inst.result:
                        constants[inst.result] = 0
                    continue

            elif inst.op == "EQ":
                if arg1 == arg2 and isinstance(arg1, str):  # x == x -> 1
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} EQ {arg2}",
                        transformed=f"{inst.result} = 1",
                        reason="Reflexive equality: x == x is always 1 (true)",
                        category="algebraic"
                    ))
                    new_inst = TACInstruction("CONST", 1, None, inst.result)
                    res.append(new_inst)
                    if inst.result:
                        constants[inst.result] = 1
                    continue

            elif inst.op == "NE":
                if arg1 == arg2 and isinstance(arg1, str):  # x != x -> 0
                    self.report.append(OptimizationRecord(
                        pass_name="Algebraic Simplification",
                        original=f"{inst.result} = {arg1} NE {arg2}",
                        transformed=f"{inst.result} = 0",
                        reason="Irreflexive inequality: x != x is always 0 (false)",
                        category="algebraic"
                    ))
                    new_inst = TACInstruction("CONST", 0, None, inst.result)
                    res.append(new_inst)
                    if inst.result:
                        constants[inst.result] = 0
                    continue

            elif inst.op == "NEG" and isinstance(arg1, (int, float)):
                folded_val = -arg1
                self.report.append(OptimizationRecord(
                    pass_name="Constant Folding",
                    original=f"{inst.result} = -{arg1}",
                    transformed=f"{inst.result} = {folded_val}",
                    reason=f"Constant negation: -({arg1}) -> {folded_val}",
                    category="constant_folding"
                ))
                new_inst = TACInstruction("CONST", folded_val, None, inst.result)
                res.append(new_inst)
                if inst.result:
                    constants[inst.result] = folded_val
                continue

            elif inst.op in ("CONST", "ASSIGN"):
                if isinstance(arg1, (int, float)):
                    if inst.result:
                        constants[inst.result] = arg1

            res.append(TACInstruction(inst.op, arg1, arg2, inst.result))

        return res

    def _dead_code_elimination(self, insts: List[TACInstruction]) -> List[TACInstruction]:
        """Removes unreachable instructions after unconditional GOTOs and redundant constant jumps."""
        res: List[TACInstruction] = []
        unreachable = False

        for inst in insts:
            if inst.op == "LABEL":
                unreachable = False
                res.append(inst)
            elif unreachable:
                # Skip unreachable instructions following unconditional GOTO
                self.report.append(OptimizationRecord(
                    pass_name="Dead Code Elimination",
                    original=str(inst),
                    transformed="(omitted)",
                    reason="Unreachable instruction following unconditional GOTO removed",
                    category="dead_code"
                ))
                continue
            elif inst.op == "JUMP_IF_FALSE":
                # If condition is constant 0 (false), IF_FALSE 0 GOTO L1 becomes unconditional GOTO L1
                if inst.arg1 == 0:
                    self.report.append(OptimizationRecord(
                        pass_name="Constant Branch Simplification",
                        original=f"IF_FALSE 0 GOTO {inst.result}",
                        transformed=f"GOTO {inst.result}",
                        reason="Branch condition is statically false (0); transformed into unconditional GOTO",
                        category="branch_simplification"
                    ))
                    res.append(TACInstruction("JUMP", None, None, inst.result))
                    unreachable = True
                # If condition is constant non-zero (true), IF_FALSE 1 GOTO L1 is never taken -> omit
                elif isinstance(inst.arg1, (int, float)) and inst.arg1 != 0:
                    self.report.append(OptimizationRecord(
                        pass_name="Dead Code Elimination",
                        original=f"IF_FALSE {inst.arg1} GOTO {inst.result}",
                        transformed="(omitted)",
                        reason=f"Branch condition is statically true ({inst.arg1}); conditional jump is never taken and eliminated",
                        category="dead_code"
                    ))
                    continue
                else:
                    res.append(inst)
            elif inst.op == "JUMP":
                res.append(inst)
                unreachable = True
            else:
                res.append(inst)

        return res


def optimize_tac(instructions: List[TACInstruction]) -> List[TACInstruction]:
    """Convenience function to optimize a list of TAC instructions."""
    optimizer = TACOptimizer(instructions)
    return optimizer.optimize()


def optimize_tac_with_report(instructions: List[TACInstruction]) -> Tuple[List[TACInstruction], List[OptimizationRecord]]:
    """Convenience function to optimize TAC instructions and retrieve detailed transformation records."""
    optimizer = TACOptimizer(instructions)
    return optimizer.optimize_with_report()


def compare_optimization(before: List[TACInstruction], after: List[TACInstruction]) -> str:
    """Returns a formatted comparison string showing BEFORE and AFTER optimization."""
    res = "=== BEFORE OPTIMIZATION ===\n"
    res += dump_tac(before) + "\n\n"
    res += "=== AFTER OPTIMIZATION ===\n"
    res += dump_tac(after)
    return res
