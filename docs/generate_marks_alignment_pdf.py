"""Generate the Sudarshan compiler evaluation criteria and marks PDF."""

from pathlib import Path
import sys
from typing import Iterable, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_pdf import SimplePDFWriter


OUTPUT = Path(__file__).resolve().parent / "Sudarshan_Compiler_Marks_Alignment_Report.pdf"


class MarksReportPDF(SimplePDFWriter):
    def bullets(self, items: Iterable[str]) -> None:
        for item in items:
            self.add_paragraph(f"- {item}")

    def table(self, rows: List[List[str]]) -> None:
        widths = [min(32, max(len(row[index]) for row in rows)) for index in range(len(rows[0]))]
        separator = "+".join("-" * (width + 2) for width in widths)
        lines = [separator]
        for row in rows:
            lines.append(
                "|".join(
                    f" {cell[:widths[index]]:<{widths[index]}} "
                    for index, cell in enumerate(row)
                )
            )
            lines.append(separator)
        self.add_code_block("\n".join(lines))

    def section(self, title: str) -> None:
        self.new_page()
        self.add_title(title)


def build_report(pdf: MarksReportPDF) -> None:
    pdf.new_page()
    pdf.add_title("SUDARSHAN")
    pdf.add_heading1("Compiler Evaluation and Marks Alignment Report")
    pdf.add_heading2("Review 2 / Phase 2 Academic Submission")
    pdf.add_code_block(
        "Project: Sudarshan - An End-to-End Compiler and Virtual Machine\n"
        "Repository: laksh1357/Sudarshan_Compiler\n"
        "Student: Lakshya Singh | Registration No.: 24BDS0054\n"
        "Course: Compiler Design\n"
        "Evaluation total: 25 marks\n"
        "Verified test result: 55 tests passed"
    )
    pdf.add_paragraph(
        "This report maps the evaluation rubric to implementation evidence in the current "
        "repository and lists the demonstrations and explanations that maximize marks."
    )

    pdf.section("1. Evaluation Summary")
    pdf.table([
        ["Criteria", "Maximum marks", "Evidence-based focus"],
        ["Implementation Progress", "7", "End-to-end working pipeline"],
        ["Technical Correctness", "5", "Correct compiler phases and VM"],
        ["Compiler Concept Application", "4", "AST, scopes, TAC, optimization"],
        ["Code Quality", "3", "Modular, readable, error-aware code"],
        ["Testing", "3", "Valid and invalid program coverage"],
        ["Individual Understanding", "3", "Architecture and design defense"],
        ["Total", "25", "Complete Review 2 demonstration"],
    ])

    pdf.section("2. Implementation Progress - 7 Marks")
    pdf.add_paragraph(
        "Maximum-mark demonstration: compile and execute a real .mini source file while "
        "showing the major intermediate stages."
    )
    pdf.add_code_block(
        "Source program\n"
        "  -> Lexer and token stream\n"
        "  -> Recursive-descent parser and AST\n"
        "  -> Semantic analysis and symbol table\n"
        "  -> Raw TAC quadruples\n"
        "  -> Optimized TAC\n"
        "  -> TAC interpreter / virtual machine\n"
        "  -> Program output"
    )
    pdf.bullets([
        "Run examples/valid.mini end to end and show its output.",
        "Use --all to display tokens, AST, symbol table, TAC, optimized TAC, and execution.",
        "Explain that the project is not only a front-end: it executes generated intermediate code.",
        "Show examples/opt_test.mini and examples/nested_scope.mini as additional evidence.",
        "Mention the optional security analysis path only as an extension; the normal pipeline remains unchanged.",
    ])
    pdf.add_code_block(
        "Recommended command:\n"
        "PYTHONPATH=src python3 src/main.py examples/valid.mini --all"
    )

    pdf.section("3. Technical Correctness - 5 Marks")
    pdf.add_paragraph(
        "The implementation contains the required compiler stages and centralized error handling."
    )
    pdf.table([
        ["Phase", "Verified implementation", "Demonstration"],
        ["Lexical analysis", "Custom location-aware lexer", "--tokens"],
        ["Parsing", "Handwritten recursive descent", "--ast"],
        ["Semantic analysis", "Type and scope validation", "--symtab"],
        ["IR generation", "TAC quadruples", "--tac"],
        ["Optimization", "Folding, propagation, DCE, identities", "--opt"],
        ["Execution", "Custom TAC VM", "Default execution"],
    ])
    pdf.bullets([
        "Explain that LexerError, ParserError, SemanticError, TACError, and CompilerRuntimeError are distinct error categories.",
        "Demonstrate a syntax error using examples/error_syntax.mini.",
        "Demonstrate a semantic error using examples/error_semantic.mini.",
        "Demonstrate a runtime error using examples/error_runtime.mini.",
        "Explain that Graphviz failure is non-fatal and does not stop compilation.",
    ])
    pdf.add_code_block(
        "Recommended commands:\n"
        "PYTHONPATH=src python3 src/main.py examples/error_syntax.mini\n"
        "PYTHONPATH=src python3 src/main.py examples/error_semantic.mini\n"
        "PYTHONPATH=src python3 src/main.py examples/error_runtime.mini"
    )

    pdf.section("4. Compiler Concept Application - 4 Marks")
    pdf.add_heading2("Abstract Syntax Tree")
    pdf.add_paragraph(
        "The parser converts tokens into typed AST nodes such as Program, VarDecl, "
        "Assignment, BinaryExpr, IfStmt, WhileStmt, and Block. The AST removes unnecessary "
        "punctuation while preserving program structure and source locations."
    )
    pdf.add_heading2("Symbol Table and Lexical Scope")
    pdf.add_paragraph(
        "Scope objects form a parent-linked chain. Lookup searches the active scope and "
        "then its parents. Same-scope duplicates are rejected and nested declarations may shadow outer names."
    )
    pdf.add_heading2("Three-Address Code")
    pdf.add_paragraph(
        "TACInstruction stores op, arg1, arg2, and result. Temporaries such as t1 and "
        "labels such as L1 make expression evaluation and control flow explicit."
    )
    pdf.add_heading2("Optimization")
    pdf.bullets([
        "Constant folding evaluates known arithmetic and comparisons at compile time.",
        "Constant propagation substitutes known values into later TAC operands.",
        "Algebraic simplification handles identities such as x + 0 and x * 1.",
        "Dead-code elimination removes instructions after unconditional jumps in linear TAC.",
        "For technical accuracy, explain that CFG-aware data-flow and runtime-error preservation remain improvement areas.",
    ])

    pdf.section("5. Code Quality - 3 Marks")
    pdf.bullets([
        "Modules are separated by compiler responsibility: lexer, parser, AST, semantic analysis, symbol table, TAC, optimizer, interpreter, and CLI.",
        "Names such as TACInstruction, SemanticAnalyzer, SymbolTable, and CompilerRuntimeError are meaningful and consistent.",
        "The project uses standard-library typing, dataclasses, enums, and structured exceptions.",
        "The CLI supports normal execution, diagnostic phase flags, --explain, --debug, and optional security analysis.",
        "Graphviz is optional and handled with a graceful fallback.",
        "Documentation should be kept synchronized with the verified 55-test state and current repository URL.",
    ])

    pdf.section("6. Testing - 3 Marks")
    pdf.add_paragraph(
        "The current repository independently verifies 55 passing unittest tests across lexer, "
        "parser, semantic analysis, TAC, optimizer, interpreter, errors, AST visualization, CLI, and security."
    )
    pdf.table([
        ["Test module", "Tests", "Coverage"],
        ["test_lexer.py", "4", "Tokens, comments, locations, lexical errors"],
        ["test_parser.py", "5", "Grammar, precedence, blocks, syntax errors"],
        ["test_semantic.py", "5", "Scopes, shadowing, declarations"],
        ["test_tac.py", "2", "Quadruples, temporaries, labels"],
        ["test_optimizer.py", "4", "Folding, identities, DCE, zero division guard"],
        ["test_interpreter.py", "8", "VM execution and runtime errors"],
        ["test_errors.py", "4", "Exception hierarchy and formatting"],
        ["test_ast_viz.py", "4", "DOT, rendering, fallback"],
        ["test_cli.py", "9", "CLI flags, errors, portability"],
        ["test_security.py", "10", "Security analysis and verified execution"],
        ["Total", "55", "All passing"],
    ])
    pdf.add_heading2("Recommended live evidence")
    pdf.add_code_block(
        "PYTHONPATH=src python3 -m unittest discover -s tests -v\n"
        "\n"
        "Expected result:\n"
        "Ran 55 tests\n"
        "OK"
    )
    pdf.add_paragraph(
        "For a stronger future submission, add raw-versus-optimized execution equivalence "
        "tests, especially for branches, loops, reassignment, and division-by-zero behavior."
    )

    pdf.section("7. Individual Understanding - 3 Marks")
    pdf.add_paragraph(
        "The following answers should be prepared for viva or project defense."
    )
    pdf.table([
        ["Question", "Answer points"],
        ["Why use TAC?", "It makes expression evaluation, temporaries, and jumps explicit."],
        ["Why use a symbol table?", "It resolves declarations, types, scopes, and shadowing."],
        ["How is precedence implemented?", "Parser call hierarchy: factor, term, additive, comparison."],
        ["How does the VM execute?", "Program counter, memory dictionary, label map, instruction dispatch."],
        ["Why optimize TAC?", "Reduce compile-time computation and simplify generated IR."],
        ["How are errors handled?", "Phase-specific exceptions with line/column diagnostics."],
        ["Why preserve raw and optimized TAC?", "It supports explanation and comparison of compiler phases."],
        ["What is not implemented?", "SSA, PGO, and real security obfuscation transformations."],
    ])

    pdf.section("8. Demonstration Checklist")
    pdf.bullets([
        "Open the repository and identify src/, tests/, examples/, and docs/.",
        "Run the complete test suite and show the passing result.",
        "Run valid.mini with --all.",
        "Display the AST and explain one BinaryExpr.",
        "Display the symbol table and explain declaration lookup.",
        "Display raw and optimized TAC and identify a folded constant.",
        "Explain one label and one conditional jump.",
        "Run the VM and explain the program counter and memory.",
        "Run syntax, semantic, and runtime error examples.",
        "Mention the optimizer correctness limitation honestly and describe the planned fix.",
    ])

    pdf.section("9. Final Marks Strategy")
    pdf.add_paragraph(
        "To maximize marks, prioritize a live, repeatable demonstration over unsupported claims. "
        "Show the implementation, connect each output to a compiler concept, and explain design "
        "choices in your own words."
    )
    pdf.table([
        ["Criterion", "Maximum-mark evidence"],
        ["Implementation Progress", "End-to-end source-to-output run with --all"],
        ["Technical Correctness", "Valid and invalid programs with phase-specific diagnostics"],
        ["Compiler Concepts", "AST, nested scopes, TAC quadruples, labels, temporaries, optimization"],
        ["Code Quality", "Modular files, type hints, exception hierarchy, readable CLI"],
        ["Testing", "55 passing tests plus live error and optimization examples"],
        ["Individual Understanding", "Explain architecture, trade-offs, limitations, and future work"],
    ])
    pdf.add_paragraph(
        "Total rubric allocation: 7 + 5 + 4 + 3 + 3 + 3 = 25 marks."
    )


def main() -> None:
    pdf = MarksReportPDF(str(OUTPUT))
    build_report(pdf)
    pdf.save()


if __name__ == "__main__":
    main()
