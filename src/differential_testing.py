"""
Differential Testing Module for Sudarshan Compiler.

Verifies that optimization passes preserve program semantics by comparing
the output of the reference interpreter (run on unoptimized TAC) against
the output of the optimized TAC through the same interpreter.

Never fabricates results — every comparison uses real execution of the
Sudarshan Virtual Machine (Interpreter).

Usage::

    result = differential_test(source_code)
    print(result.summary())

Or to test a specific optimization level::

    result = differential_test_level(source_code, level="O3")
"""

from __future__ import annotations

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from tac import TACGenerator, TACInstruction, dump_tac
from interpreter import Interpreter
from advanced_optimizer import OptimizationPassManager, OptimizationReport


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class DiffTestCase:
    """
    Result of a single differential test (one source program, one opt level).
    """
    level: str
    source_code: str
    reference_output: List[Any]
    optimized_output: List[Any]
    passed: bool
    failure_reason: Optional[str] = None
    raw_tac_text: str = ""
    opt_tac_text: str = ""
    opt_report: Optional[OptimizationReport] = None
    error: Optional[str] = None

    def summary(self) -> str:
        status = "PASS ✓" if self.passed else f"FAIL ✗  ({self.failure_reason})"
        lines = [
            f"  Level {self.level}: {status}",
            f"    Reference output : {self.reference_output}",
            f"    Optimized output : {self.optimized_output}",
        ]
        if self.error:
            lines.append(f"    Error : {self.error}")
        return "\n".join(lines)


@dataclass
class DiffTestSuite:
    """
    Aggregated results for multiple levels run on the same source.
    """
    source_code: str
    cases: List[DiffTestCase] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.cases)

    def summary(self) -> str:
        passed = sum(1 for c in self.cases if c.passed)
        lines = [
            f"=== Differential Testing Report ===",
            f"  Tests run    : {len(self.cases)}",
            f"  Tests passed : {passed}",
            f"  Tests failed : {len(self.cases) - passed}",
            "",
        ]
        for case in self.cases:
            lines.append(case.summary())
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reference execution
# ---------------------------------------------------------------------------

def _compile_to_tac(source_code: str) -> Tuple[List[TACInstruction], Optional[str]]:
    """
    Run lexer → parser → semantic analyzer → TAC generator on source_code.
    Returns (instructions, None) on success, or ([], error_message) on failure.
    """
    try:
        tokens = Lexer(source_code).tokenize()
        ast = Parser(tokens).parse()
        SemanticAnalyzer().analyze(ast)
        tac = TACGenerator().generate(ast)
        return tac, None
    except Exception as exc:
        return [], str(exc)


def _execute_tac(instructions: List[TACInstruction], max_steps: int = 100_000) -> Tuple[List[Any], Optional[str]]:
    """
    Execute a TAC instruction list through the Sudarshan VM.
    Returns (output_list, None) on success, or ([], error_message) on failure.
    """
    try:
        vm = Interpreter(instructions, max_steps=max_steps)
        output = vm.run()
        return output, None
    except Exception as exc:
        return [], str(exc)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def differential_test_level(
    source_code: str,
    level: str = "O2",
    max_steps: int = 100_000,
) -> DiffTestCase:
    """
    Test that optimization level `level` preserves the semantics of source_code.

    Steps:
      1. Compile to TAC (reference).
      2. Execute reference TAC → reference_output.
      3. Optimize TAC at the given level → optimized TAC.
      4. Execute optimized TAC → optimized_output.
      5. Compare reference_output == optimized_output.
    """
    raw_tac, compile_err = _compile_to_tac(source_code)
    if compile_err:
        return DiffTestCase(
            level=level,
            source_code=source_code,
            reference_output=[],
            optimized_output=[],
            passed=False,
            failure_reason="compilation_error",
            error=compile_err,
        )

    ref_output, ref_err = _execute_tac(raw_tac, max_steps)
    if ref_err:
        return DiffTestCase(
            level=level,
            source_code=source_code,
            reference_output=[],
            optimized_output=[],
            passed=False,
            failure_reason="reference_execution_error",
            error=ref_err,
            raw_tac_text=dump_tac(raw_tac),
        )

    # Optimize
    try:
        manager = OptimizationPassManager(level=level)
        opt_tac, opt_report = manager.run(raw_tac)
    except Exception as exc:
        return DiffTestCase(
            level=level,
            source_code=source_code,
            reference_output=ref_output,
            optimized_output=[],
            passed=False,
            failure_reason="optimization_error",
            error=str(exc),
            raw_tac_text=dump_tac(raw_tac),
        )

    opt_output, opt_err = _execute_tac(opt_tac, max_steps)

    passed = (not opt_err) and (ref_output == opt_output)
    failure_reason = None
    if opt_err:
        failure_reason = f"optimized_execution_error: {opt_err}"
    elif ref_output != opt_output:
        failure_reason = (
            f"output_mismatch: reference={ref_output!r} optimized={opt_output!r}"
        )

    return DiffTestCase(
        level=level,
        source_code=source_code,
        reference_output=ref_output,
        optimized_output=opt_output,
        passed=passed,
        failure_reason=failure_reason,
        raw_tac_text=dump_tac(raw_tac),
        opt_tac_text=dump_tac(opt_tac),
        opt_report=opt_report,
        error=opt_err,
    )


def differential_test(
    source_code: str,
    levels: Optional[List[str]] = None,
    max_steps: int = 100_000,
) -> DiffTestSuite:
    """
    Run differential tests across multiple optimization levels.

    Args:
        source_code: Sudarshan source to compile and test.
        levels:      List of optimization levels to test. Default: all four.
        max_steps:   VM execution step limit (infinite-loop guard).

    Returns:
        A DiffTestSuite with one DiffTestCase per level.
    """
    if levels is None:
        levels = ["O0", "O1", "O2", "O3"]

    suite = DiffTestSuite(source_code=source_code)
    for level in levels:
        case = differential_test_level(source_code, level=level, max_steps=max_steps)
        suite.cases.append(case)
    return suite
