"""
Compiler Service Integration Layer for Sudarshan Compiler Studio.

Safely orchestrates all compiler pipeline phases:
1. Lexical Analysis
2. Syntax Analysis (AST)
3. Semantic Analysis (Symbol Table)
4. TAC Generation
5. TAC Optimization & Report Generation
6. Virtual Machine Execution
"""

import os
import sys
import time
import io
from contextlib import redirect_stdout
from typing import List, Optional, Tuple

# Ensure src/ is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from errors import (
    SudarshanError, LexerError, ParserError, SemanticError,
    TACError, CompilerRuntimeError
)
from lexer import Lexer
from parser import Parser
from ast_nodes import dump_ast, export_ast_dot, ast_to_dict
from semantic import SemanticAnalyzer
from tac import TACGenerator, TACInstruction, dump_tac
from tac_opt import optimize_tac_with_report
from interpreter import Interpreter

from .schemas import (
    CompilationResponse, TokenModel, SymbolModel, ScopeModel,
    SymbolTableModel, SemanticDiagnosticModel, TACInstructionModel,
    OptimizationRecordModel, OptimizationStatsModel, CompilerErrorModel,
    TimingModel
)


def _extract_source_context(source: str, line: Optional[int], column: Optional[int]) -> Optional[str]:
    """Extracts a short snippet of the source code around the given error line."""
    if not source or line is None or line < 1:
        return None
    lines = source.splitlines()
    if 1 <= line <= len(lines):
        err_line = lines[line - 1]
        col = column if column is not None and column > 0 else 1
        pointer = " " * (col - 1) + "^"
        return f"{err_line}\n{pointer}"
    return None


def serialize_tac_instructions(instructions: List[TACInstruction]) -> List[TACInstructionModel]:
    """Converts internal TACInstruction objects to API models."""
    res: List[TACInstructionModel] = []
    for idx, inst in enumerate(instructions, start=1):
        res.append(TACInstructionModel(
            index=idx,
            op=inst.op,
            arg1=inst.arg1,
            arg2=inst.arg2,
            result=inst.result,
            text=str(inst)
        ))
    return res


def compile_sudarshan(
    source_code: str,
    optimize: bool = True,
    max_steps: int = 100000,
    execute: bool = False
) -> CompilationResponse:
    """
    Executes the Sudarshan compiler pipeline in strict phase order.
    Never fabricates results. Earlier successful phase results are preserved
    if a subsequent phase fails.
    """
    start_total = time.perf_counter()
    timing = TimingModel()

    # Response accumulator
    resp = CompilationResponse(
        success=False,
        timing=timing
    )

    # ==========================================
    # Phase 1: Lexical Analysis
    # ==========================================
    t0 = time.perf_counter()
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        timing.lexical_ms = round((time.perf_counter() - t0) * 1000, 3)

        resp.tokens = [
            TokenModel(
                type=tok.type.name,
                value=tok.value,
                line=tok.line,
                column=tok.column
            )
            for tok in tokens
        ]
    except LexerError as err:
        timing.lexical_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "lexical"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="lexical",
            error_type="LexerError",
            message=err.message,
            line=err.line,
            column=err.column,
            source_context=_extract_source_context(source_code, err.line, err.column)
        ))
        return resp
    except Exception as err:
        timing.lexical_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "lexical"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="lexical",
            error_type=err.__class__.__name__,
            message=str(err),
            line=None,
            column=None,
            source_context=None
        ))
        return resp

    # ==========================================
    # Phase 2: Syntax Analysis (Parser & AST)
    # ==========================================
    t0 = time.perf_counter()
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        timing.syntax_ms = round((time.perf_counter() - t0) * 1000, 3)

        resp.ast = ast_to_dict(ast)
        resp.ast_text = dump_ast(ast)
        resp.ast_dot = export_ast_dot(ast)
    except ParserError as err:
        timing.syntax_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "syntax"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="syntax",
            error_type="ParserError",
            message=err.message,
            line=err.line,
            column=err.column,
            source_context=_extract_source_context(source_code, err.line, err.column)
        ))
        return resp
    except Exception as err:
        timing.syntax_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "syntax"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="syntax",
            error_type=err.__class__.__name__,
            message=str(err),
            line=None,
            column=None,
            source_context=None
        ))
        return resp

    # ==========================================
    # Phase 3: Semantic Analysis & Symbol Table
    # ==========================================
    t0 = time.perf_counter()
    try:
        analyzer = SemanticAnalyzer()
        symtab = analyzer.analyze(ast)
        timing.semantic_ms = round((time.perf_counter() - t0) * 1000, 3)

        # Convert SymbolTable to schema
        sym_dict = symtab.to_dict()
        scopes_list = [
            ScopeModel(
                scope_level=s["scope_level"],
                symbols=[SymbolModel(**sym) for sym in s["symbols"]]
            )
            for s in sym_dict.get("scopes", [])
        ]
        all_syms = [SymbolModel(**sym) for sym in sym_dict.get("symbols", [])]

        resp.symbol_table = SymbolTableModel(
            scopes=scopes_list,
            symbols=all_syms
        )
        resp.semantic_diagnostics.append(SemanticDiagnosticModel(
            severity="info",
            message=f"Semantic validation passed successfully ({len(all_syms)} symbol declarations verified).",
            line=None,
            column=None
        ))
    except SemanticError as err:
        timing.semantic_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "semantic"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="semantic",
            error_type="SemanticError",
            message=err.message,
            line=err.line,
            column=err.column,
            source_context=_extract_source_context(source_code, err.line, err.column)
        ))
        resp.semantic_diagnostics.append(SemanticDiagnosticModel(
            severity="error",
            message=err.message,
            line=err.line,
            column=err.column
        ))
        return resp
    except Exception as err:
        timing.semantic_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "semantic"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="semantic",
            error_type=err.__class__.__name__,
            message=str(err),
            line=None,
            column=None,
            source_context=None
        ))
        return resp

    # ==========================================
    # Phase 4: Intermediate Code Generation (TAC)
    # ==========================================
    t0 = time.perf_counter()
    try:
        tac_gen = TACGenerator()
        raw_tac = tac_gen.generate(ast)
        timing.tac_ms = round((time.perf_counter() - t0) * 1000, 3)

        resp.raw_tac = serialize_tac_instructions(raw_tac)
        resp.raw_tac_text = dump_tac(raw_tac)
    except TACError as err:
        timing.tac_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "tac"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="tac",
            error_type="TACError",
            message=err.message,
            line=err.line,
            column=err.column,
            source_context=_extract_source_context(source_code, err.line, err.column)
        ))
        return resp
    except Exception as err:
        timing.tac_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "tac"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="tac",
            error_type=err.__class__.__name__,
            message=str(err),
            line=None,
            column=None,
            source_context=None
        ))
        return resp

    # ==========================================
    # Phase 4b: TAC Optimization Pass
    # ==========================================
    t0 = time.perf_counter()
    try:
        if optimize:
            opt_tac, opt_reports = optimize_tac_with_report(raw_tac)
        else:
            opt_tac = raw_tac
            opt_reports = []

        timing.optimization_ms = round((time.perf_counter() - t0) * 1000, 3)

        resp.optimized_tac = serialize_tac_instructions(opt_tac)
        resp.optimized_tac_text = dump_tac(opt_tac)
        resp.optimization_report = [
            OptimizationRecordModel(
                pass_name=r.pass_name,
                original=r.original,
                transformed=r.transformed,
                reason=r.reason,
                category=r.category
            )
            for r in opt_reports
        ]

        raw_count = len(raw_tac)
        opt_count = len(opt_tac)
        diff = raw_count - opt_count
        reduction_pct = round((diff / raw_count) * 100, 1) if raw_count > 0 else 0.0

        resp.optimization_stats = OptimizationStatsModel(
            original_count=raw_count,
            optimized_count=opt_count,
            reduction_percentage=reduction_pct,
            transformations_count=len(opt_reports)
        )
    except Exception as err:
        timing.optimization_ms = round((time.perf_counter() - t0) * 1000, 3)
        timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
        resp.failed_phase = "optimization"
        resp.compilation_errors.append(CompilerErrorModel(
            phase="optimization",
            error_type=err.__class__.__name__,
            message=str(err),
            line=None,
            column=None,
            source_context=None
        ))
        return resp

    # Compilation succeeded through all IR stages
    resp.success = True

    # ==========================================
    # Phase 5: Virtual Machine Execution (optional)
    # ==========================================
    if execute:
        t0 = time.perf_counter()
        target_tac = opt_tac if optimize else raw_tac
        vm = Interpreter(target_tac, max_steps=max_steps)

        stdout_buf = io.StringIO()
        try:
            with redirect_stdout(stdout_buf):
                output_vals = vm.run()

            timing.execution_ms = round((time.perf_counter() - t0) * 1000, 3)
            resp.execution_status = "success"
            resp.program_output = output_vals
            resp.stdout_text = stdout_buf.getvalue()
            resp.execution_steps = vm.step_count
        except CompilerRuntimeError as err:
            timing.execution_ms = round((time.perf_counter() - t0) * 1000, 3)
            resp.execution_status = "step_limit_exceeded" if "step limit exceeded" in err.message.lower() else "error"
            resp.program_output = vm.output
            resp.stdout_text = stdout_buf.getvalue()
            resp.execution_steps = vm.step_count
            resp.runtime_errors.append(CompilerErrorModel(
                phase="execution",
                error_type="CompilerRuntimeError",
                message=err.message,
                line=err.line,
                column=err.column,
                source_context=None
            ))
        except Exception as err:
            timing.execution_ms = round((time.perf_counter() - t0) * 1000, 3)
            resp.execution_status = "error"
            resp.program_output = vm.output
            resp.stdout_text = stdout_buf.getvalue()
            resp.execution_steps = vm.step_count
            resp.runtime_errors.append(CompilerErrorModel(
                phase="execution",
                error_type=err.__class__.__name__,
                message=str(err),
                line=None,
                column=None,
                source_context=None
            ))

    timing.total_ms = round((time.perf_counter() - start_total) * 1000, 3)
    return resp
