"""
Main Command-Line Driver for Sudarshan Compiler.

Integrates Lexer, Parser, Semantic Analyzer, TAC Generator, TAC Optimizer, and Interpreter.
Supports phase flags: --tokens, --ast, --symtab, --tac, --opt, --explain, --all.
Handles compiler errors cleanly without Python tracebacks.
"""

import argparse
import os
import sys

# Ensure current directory is in Python path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from errors import LexerError, ParserError, SemanticError, TACError, CompilerRuntimeError, SudarshanError, MiniLangError, CompilerError
from lexer import Lexer
from parser import Parser
from ast_nodes import dump_ast, render_ast_graph
from semantic import SemanticAnalyzer
from tac import TACGenerator, dump_tac
from tac_opt import optimize_tac, compare_optimization
from interpreter import Interpreter
from security import (
    SecurityConfig,
    SecurityPass,
    SecureInterpreter,
    analyze_block,
    build_cfg,
    format_report,
    protect_ir,
    score_features,
    select_policy,
)


def print_explanation(filename: str, source_code: str, tokens: list, ast, symtab, raw_tac: list, opt_tac: list):
    """Prints a detailed educational explanation of how the compiler processed the program."""
    print("==================================================")
    print("      SUDARSHAN COMPILER PIPELINE EXPLANATION     ")
    print("==================================================")
    print(f"File: {filename}\n")

    print("1. LEXICAL ANALYSIS (lexer.py)")
    print(f"   • Scanned {len(source_code)} source characters into {len(tokens)} token objects.")
    print("   • Stripped comments and whitespace, categorized keywords, numbers, operators, and symbols.")
    print("   • Tracked line & column positions for precise error reporting.\n")

    print("2. SYNTAX ANALYSIS (parser.py)")
    print("   • LL(1) Recursive Descent parsing matched the BNF grammar.")
    print("   • Generated AST hierarchy maintaining mathematical operator precedence (*, / over +, -).\n")

    print("3. SEMANTIC ANALYSIS (semantic.py & symbol_table.py)")
    print("   • Verified static semantics and lexical block scopes using Scope parent-pointers.")
    print(f"   • Verified symbol declarations in Symbol Table: {list(symtab.global_scope.symbols.keys())}\n")

    print("4. INTERMEDIATE CODE GENERATION (tac.py)")
    print(f"   • Flattened AST into {len(raw_tac)} Three-Address Code quadruples.")
    print("   • Allocated temporary registers (t1, t2...) and jump labels (L1, L2...).\n")

    print("5. TAC OPTIMIZATION (tac_opt.py)")
    print(f"   • Applied Constant Folding & Propagation, producing {len(opt_tac)} optimized quadruples.")
    print("   • Simplifies compile-time arithmetic without affecting execution semantics.\n")

    print("6. VIRTUAL MACHINE EXECUTION (interpreter.py)")
    print("   • Executed linear quadruples on a Von Neumann virtual machine simulation.")
    print("   • Program Output:")


def main():
    cli_parser = argparse.ArgumentParser(
        description="Sudarshan Compiler & Interpreter CLI Driver",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./sudarshan examples/valid.mini
  ./sudarshan examples/valid.mini --all
  ./sudarshan examples/valid.mini --explain
  ./sudarshan examples/valid.mini --tokens --ast --viz
  ./sudarshan examples/error_syntax.mini
"""
    )
    cli_parser.add_argument("filename", help="Path to the .mini source code file")
    cli_parser.add_argument("--tokens", action="store_true", help="Display token stream from Lexer")
    cli_parser.add_argument("--ast", action="store_true", help="Display Abstract Syntax Tree (AST)")
    cli_parser.add_argument("--viz", action="store_true", help="Render AST to image file (ast_tree.png) using Graphviz if available")
    cli_parser.add_argument("--symtab", action="store_true", help="Display Symbol Table and scopes")

    cli_parser.add_argument("--tac", action="store_true", help="Display generated Three-Address Code (TAC)")
    cli_parser.add_argument("--opt", action="store_true", help="Display optimized Three-Address Code")
    cli_parser.add_argument("--explain", action="store_true", help="Display detailed educational explanation of all phases")
    cli_parser.add_argument("--all", action="store_true", help="Display all compiler pipeline phases and execution output")
    cli_parser.add_argument(
        "--secure",
        "--security",
        dest="secure",
        action="store_true",
        help="Enable the optional security pass",
    )
    cli_parser.add_argument(
        "--adaptive-security",
        action="store_true",
        help="Enable the security pass in adaptive mode",
    )
    cli_parser.add_argument(
        "--security-report",
        action="store_true",
        help="Display security analysis information",
    )
    cli_parser.add_argument(
        "--dump-protected-ir",
        action="store_true",
        help="Display IR after the security pass",
    )
    cli_parser.add_argument("--debug", action="store_true", help="Preserve full Python tracebacks for compiler debugging")


    args = cli_parser.parse_args()

    # If --all is passed, enable all phase flags
    if args.all:
        args.tokens = True
        args.ast = True
        args.symtab = True
        args.tac = True
        args.opt = True

    # If no phase flags are set, run standard execution mode
    security_requested = (
        args.secure
        or args.adaptive_security
        or args.security_report
        or args.dump_protected_ir
    )
    run_execution_only = not (
        args.tokens
        or args.ast
        or args.symtab
        or args.tac
        or args.opt
        or args.explain
    )

    if not os.path.exists(args.filename):
        print(f"Error: Source file '{args.filename}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(args.filename, "r", encoding="utf-8") as f:
        source_code = f.read()

    # --- Phase 1: Lexical Analysis ---
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        if args.tokens:
            print("==================================================")
            print("         PHASE 1: LEXICAL ANALYSIS (TOKENS)       ")
            print("==================================================")
            for tok in tokens:
                print(f"  {tok}")
            print()
    except LexerError as err:
        print(f"\n❌ LEXICAL ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # --- Phase 2: Syntax Analysis ---
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        if args.ast or args.viz:
            print("==================================================")
            print("        PHASE 2: SYNTAX ANALYSIS (AST TREE)       ")
            print("==================================================")
            if args.ast:
                print(dump_ast(ast))
            if args.viz:
                render_ast_graph(ast)
            print()

    except ParserError as err:
        print(f"\n❌ SYNTAX ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # --- Phase 3: Semantic Analysis ---
    try:
        semantic = SemanticAnalyzer()
        symtab = semantic.analyze(ast)
        if args.symtab:
            print("==================================================")
            print("       PHASE 3: SEMANTIC ANALYSIS (SYMBOL TABLE)  ")
            print("==================================================")
            print(symtab.dump())
            print()
    except SemanticError as err:
        print(f"\n❌ SEMANTIC ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # --- Phase 4: Intermediate Code Generation (TAC) & Optimization ---
    try:
        tac_gen = TACGenerator()
        raw_tac = tac_gen.generate(ast)
        if args.tac:
            print("==================================================")
            print("     PHASE 4: THREE-ADDRESS CODE (UNOPTIMIZED)    ")
            print("==================================================")
            print(dump_tac(raw_tac))
            print()

        opt_tac = optimize_tac(raw_tac)
        if args.opt:
            print("==================================================")
            print("     PHASE 4b: THREE-ADDRESS CODE (OPTIMIZED)     ")
            print("==================================================")
            print(dump_tac(opt_tac))
            print()

        protected_tac = opt_tac
        protected_program = None
        security_config = SecurityConfig(
            enabled=security_requested,
            adaptive=args.adaptive_security,
        )
        if security_requested:
            protected_tac = SecurityPass(security_config).transform(opt_tac)
            cfg = build_cfg(protected_tac)
            features = [analyze_block(block) for block in cfg.blocks]
            scores = [score_features(feature) for feature in features]
            policies = [select_policy(score) for score in scores]
            protected_program = protect_ir(protected_tac, policies)
            if args.security_report:
                print(f"Security enabled: {security_config.enabled}")
                print(f"Adaptive security: {security_config.adaptive}")
                print(format_report(features, scores, policies))
            if args.dump_protected_ir:
                print("==================================================")
                print("             PROTECTED INTERMEDIATE REPRESENTATION ")
                print("==================================================")
                print(dump_tac(protected_tac))
                print()
    except TACError as err:
        if args.debug:
            raise
        print(f"\n❌ TAC GENERATION ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    # --- Phase 5: Virtual Machine Execution / Interpretation ---
    try:
        if args.explain:
            print_explanation(args.filename, source_code, tokens, ast, symtab, raw_tac, opt_tac)
            vm = SecureInterpreter(protected_program) if protected_program else Interpreter(protected_tac)
            vm.run()
            print("\n✅ Execution finished successfully.")
        elif args.all or run_execution_only:
            print("==================================================")
            print("         PHASE 5: VIRTUAL MACHINE EXECUTION       ")
            print("==================================================")
            print("Program Output:")
            vm = SecureInterpreter(protected_program) if protected_program else Interpreter(protected_tac)
            vm.run()
            print("\n✅ Execution finished successfully.")
    except CompilerRuntimeError as err:
        if args.debug:
            raise
        print(f"\n❌ RUNTIME ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    except SudarshanError as err:
        if args.debug:
            raise
        print(f"\n❌ COMPILER ERROR: {err}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()
