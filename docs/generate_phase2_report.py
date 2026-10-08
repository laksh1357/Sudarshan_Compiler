"""Generate the Phase 2 compiler implementation progress report.

This generator uses the repository's dependency-free PDF writer. Project-specific
claims are limited to the current source tree, test suite, and verified examples.
"""

from pathlib import Path
import sys
from typing import Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_pdf import SimplePDFWriter


OUTPUT = Path(__file__).resolve().parent / "Phase2_Core_Implementation_Progress_Report.pdf"


class ReportPDF(SimplePDFWriter):
    """Small report-oriented extension of the existing PDF writer."""

    def add_bullets(self, items: Iterable[str]) -> None:
        for item in items:
            self.add_paragraph(f"- {item}")

    def add_placeholder(self, label: str) -> None:
        self.add_code_block(f"[{label}]")

    def add_table(self, rows: List[List[str]], widths: Optional[List[int]] = None) -> None:
        if not rows:
            return
        widths = widths or [max(len(row[column]) for row in rows) for column in range(len(rows[0]))]
        widths = [min(width, 34) for width in widths]
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

    def add_section(self, number: str, title: str) -> None:
        self.new_page()
        self.add_title(f"{number}. {title}")


def architecture_diagram() -> str:
    return (
        "Source Program (.mini)\n"
        "        |\n"
        "      Lexer -> Tokens\n"
        "        |\n"
        "     Parser -> AST\n"
        "        |\n"
        "Semantic Analyzer -> Symbol Table\n"
        "        |\n"
        "  TAC Generator -> TAC\n"
        "        |\n"
        "TAC Optimizer -> Optimized TAC\n"
        "        |\n"
        " Interpreter / Virtual Machine\n"
        "        |\n"
        "    Program Output"
    )


def build_report(pdf: ReportPDF, toc_pages: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    pages: Dict[str, int] = {}
    pdf.new_page()
    pdf.add_title("SUDARSHAN")
    pdf.add_heading1("An End-to-End Compiler and Virtual Machine")
    pdf.add_heading2("Phase 2: Core Implementation & Review 2")
    pdf.add_heading2("Implementation Progress Report")
    pdf.add_code_block(
        "Student Name: [NAME]\n"
        "Registration Number: [REGISTRATION NUMBER]\n"
        "Programme: B.Tech Computer Science and Engineering\n"
        "Specialization: Data Science\n"
        "University: Vellore Institute of Technology (VIT)\n"
        "Course: Compiler Design\n"
        "Faculty: [FACULTY NAME]\n"
        "Academic Year: 2026-27\n"
        "Review: Review 2 | Phase: Phase 2 - Core Implementation"
    )
    pdf.add_paragraph(
        "This report documents the currently implemented compiler pipeline, its "
        "intermediate representation, optimization, virtual machine, tests, and "
        "the initial opt-in security analysis layer."
    )
    pdf.add_placeholder("INSERT INSTITUTION / PROJECT COVER SCREENSHOT")

    pdf.new_page()
    pdf.add_title("Table of Contents")
    toc = [
        ("1", "Project Overview"), ("2", "Phase 2 Objective"), ("3", "System Architecture"),
        ("4", "Lexical Analysis"), ("5", "Syntax Analysis"), ("6", "Abstract Syntax Tree"),
        ("7", "Semantic Analysis"), ("8", "Symbol Table"), ("9", "Intermediate Code Generation"),
        ("10", "Optimization"), ("11", "Virtual Machine / Execution Engine"),
        ("12", "Error Handling"), ("13", "Testing"), ("14", "Implementation Progress"),
        ("15", "Code Quality"), ("16", "Technical Challenges and Problem Solving"),
        ("17", "Compiler Concept Application"), ("18", "Functional Demonstration"),
        ("19", "Review 2 Marks Alignment"), ("20", "Individual Understanding / Viva Preparation"),
        ("21", "Future Enhancements"), ("22", "Conclusion"), ("A", "Project Directory Structure"),
        ("B", "Screenshots"), ("C", "Source Code References"),
    ]
    for number, title in toc:
        page = toc_pages.get(number, "[PAGE]") if toc_pages else "[PAGE]"
        pdf.add_paragraph(f"{number}. {title} ........................................ {page}")

    sections = {
        "1": ("Project Overview", [
            "Sudarshan is an end-to-end imperative compiler and virtual machine implemented in Python 3 without parser generators.",
            "The implementation demonstrates a complete path from source text through lexical analysis, recursive-descent parsing, AST construction, semantic validation, TAC generation, optimization, and interpretation.",
            "The verified example program produces the outputs 15 and 115. These values are included as execution evidence; no additional performance claims are made here.",
        ]),
        "2": ("Phase 2 Objective", [
            "Phase 2 focuses on implementing the major functional compiler components and integrating them into a working execution pipeline.",
            "Evidence includes source modules, example programs, intermediate representations, error paths, automated tests, CLI diagnostics, and the end-to-end virtual machine run.",
            "The report maps implementation evidence to the Review 2 criteria: implementation progress, technical correctness, compiler concept application, code quality, testing, and individual understanding.",
        ]),
        "3": ("System Architecture", []),
        "4": ("Lexical Analysis", [
            "The lexer scans source characters and emits location-aware tokens. It recognizes keywords, identifiers, integer literals, arithmetic and comparison operators, assignment, delimiters, comments, and EOF.",
            "Invalid characters and malformed standalone exclamation marks raise LexerError with line and column information.",
            "Example: x = 10 + 5; becomes ID(x), ASSIGN(=), NUMBER(10), PLUS(+), NUMBER(5), SEMICOLON(;).",
        ]),
        "5": ("Syntax Analysis", [
            "The parser is a hand-written recursive-descent parser with precedence levels for comparison, addition/subtraction, multiplication/division, and factors.",
            "It consumes the token stream and constructs AST nodes for declarations, assignments, print statements, conditionals, loops, blocks, unary expressions, and binary expressions.",
            "Unexpected statement starts, missing delimiters, and malformed expression factors produce ParserError diagnostics.",
        ]),
        "6": ("Abstract Syntax Tree", [
            "The AST represents source structure without retaining unnecessary punctuation. Nodes preserve source line and column information.",
            "Representative structure:",
        ]),
        "7": ("Semantic Analysis", [
            "SemanticAnalyzer validates declaration-before-use, duplicate declarations in the active scope, assignment compatibility, expression operands, print expressions, and control-flow conditions.",
            "The language currently models integer expressions and integer-valued comparisons. SemanticError reports the relevant source location.",
            "Example invalid cases include using an undeclared variable and redeclaring a name in the same scope.",
        ]),
        "8": ("Symbol Table", [
            "SymbolTable maintains nested Scope objects with parent links. Symbols record name, type, source location, and scope level.",
            "Lookup searches from the active scope toward the global scope, while lookup_current_scope supports duplicate-declaration checks. Shadowing is supported in nested blocks.",
        ]),
        "9": ("Intermediate Code Generation", [
            "The TAC generator lowers AST nodes to a linear list of quadruple-like TACInstruction objects: (op, arg1, arg2, result).",
            "Temporaries use names such as t1 and t2; control flow uses LABEL, JUMP, and JUMP_IF_FALSE instructions. Nested variables use scope suffixes such as x_s1.",
            "Example source: x = 10 + 5; is represented conceptually as t1 = 10, t2 = 5, t3 = t1 ADD t2, x = t3.",
        ]),
        "10": ("Optimization", [
            "The TAC optimizer performs constant folding and propagation, algebraic identity simplification, branch simplification, and dead-code elimination.",
            "Division by zero is not folded away, preserving a runtime error for the interpreter. Existing optimization tests cover folding, identities, safe division handling, and unreachable code.",
        ]),
        "11": ("Virtual Machine / Execution Engine", [
            "The interpreter executes optimized TAC sequentially with a program counter, dictionary-backed memory, a label map, and an output list.",
            "It evaluates constants, variables, temporaries, arithmetic, comparisons, unary negation, printing, and explicit branches. It raises CompilerRuntimeError for invalid operations, undefined operands, invalid labels, and division by zero.",
            "Verified execution evidence from examples/valid.mini:",
        ]),
        "12": ("Error Handling", [
            "Lexical errors are detected by Lexer during tokenization.",
            "Syntax errors are detected by Parser during grammar consumption.",
            "Semantic errors are detected before TAC generation.",
            "Runtime errors are raised by the interpreter. The CLI prints phase-specific diagnostics and exits with status 1 for handled compiler/runtime failures.",
        ]),
        "13": ("Testing", [
            "The current repository test run contains 55 passing unit and integration tests using Python unittest discovery.",
            "Coverage includes lexer, parser, semantic analysis, TAC generation, optimization, interpreter execution, error formatting, AST visualization, CLI behavior, and the security subsystem.",
            "The report does not use the older 22-test figure because it is not supported by the current repository state.",
        ]),
        "14": ("Implementation Progress", [
            "The following status reflects the current source tree rather than an assumed older architecture.",
        ]),
        "15": ("Code Quality", [
            "The repository separates compiler stages into focused modules under src/, keeps tests under tests/, and provides examples and documentation under dedicated directories.",
            "The implementation uses standard-library Python, type hints in core modules, centralized errors, reusable TAC formatting, and explicit CLI phase flags.",
        ]),
        "16": ("Technical Challenges and Problem Solving", [
            "Evidence-supported implementation challenges include preserving source locations through diagnostics, managing nested scopes, lowering structured branches to labels and jumps, optimizing without changing division-by-zero behavior, and keeping CLI/Graphviz failures explicit.",
            "Security extension challenge: the repository had no pre-existing CFG or SSA module, so the security layer derives a CFG from optimized TAC without rewriting the compiler frontend or interpreter semantics.",
        ]),
        "17": ("Compiler Concept Application", [
            "The implementation directly connects standard compiler theory to executable modules and observable intermediate results.",
        ]),
        "18": ("Functional Demonstration", [
            "The end-to-end demonstration should be conducted using examples/valid.mini and the existing CLI flags. Each stage can be captured for the final evaluation record.",
            "The known verified output is 15 followed by 115.",
        ]),
        "19": ("Review 2 Marks Alignment", [
            "The project addresses the rubric through working modules, intermediate outputs, execution evidence, modular source organization, and automated tests.",
        ]),
        "20": ("Individual Understanding / Viva Preparation", [
            "The questions below are concise preparation prompts grounded in the current implementation.",
        ]),
        "21": ("Future Enhancements", [
            "Potential future work includes functions, richer types, additional optimizations, stronger debugging support, CFG visualization, profile-guided optimization, and real security transformations.",
            "The current security package intentionally stops at derived analysis, policy selection, identity transformation, integrity metadata, and verified reuse of the existing VM.",
        ]),
        "22": ("Conclusion", [
            "Phase 2 demonstrates a functioning end-to-end compiler pipeline rather than isolated source files. The lexer, parser, AST, semantic analyzer, symbol table, TAC generator, optimizer, interpreter, CLI, examples, and tests are integrated.",
            "The verified 15 and 115 execution results provide concrete functional evidence. The security extension is opt-in and preserves the normal pipeline while establishing a research-oriented analysis and verification boundary.",
        ]),
        "A": ("Project Directory Structure", []),
        "B": ("Screenshots", []),
        "C": ("Source Code References", []),
    }

    for number, (title, paragraphs) in sections.items():
        pages[number] = pdf.page_number + 1
        pdf.add_section(number, title)
        for paragraph in paragraphs:
            pdf.add_paragraph(paragraph)
        if number == "3":
            pdf.add_code_block(architecture_diagram())
            pdf.add_table([
                ["Module", "Input", "Processing", "Output", "Status"],
                ["Lexer", "Source text", "Token scanning", "Tokens", "Implemented"],
                ["Parser", "Tokens", "Recursive descent", "AST", "Implemented"],
                ["Semantic", "AST", "Scope/type checks", "Validated AST", "Implemented"],
                ["TAC", "AST", "Lowering", "TAC list", "Implemented"],
                ["Optimizer", "TAC", "Folding/DCE", "Optimized TAC", "Implemented"],
                ["VM", "TAC", "Interpretation", "Output", "Implemented"],
            ])
        elif number == "6":
            pdf.add_code_block("Assignment\n|-- Identifier: x\n`-- Binary Expression\n    |-- IntegerLiteral(10)\n    `-- IntegerLiteral(5)")
            pdf.add_placeholder("INSERT AST SCREENSHOT")
        elif number == "8":
            pdf.add_table([
                ["Identifier", "Type", "Scope", "Information"],
                ["sum", "int", "global", "Declared symbol"],
                ["bonus", "int", "nested", "Scope-mangled as bonus_s1"],
            ])
        elif number == "11":
            pdf.add_code_block("Program Output:\n15\n115")
            pdf.add_placeholder("INSERT TERMINAL EXECUTION SCREENSHOT")
        elif number == "13":
            pdf.add_table([
                ["Category", "Current evidence"],
                ["Lexical", "4 tests"],
                ["Parser", "5 tests"],
                ["Semantic", "5 tests"],
                ["TAC", "2 tests"],
                ["Optimizer", "4 tests"],
                ["Interpreter", "8 tests"],
                ["Errors", "4 tests"],
                ["AST/CLI", "13 tests"],
                ["Security", "10 tests"],
                ["Total", "55 passing tests"],
            ])
            pdf.add_placeholder("INSERT AUTOMATED TEST RESULTS SCREENSHOT")
        elif number == "14":
            pdf.add_table([
                ["Module", "Status", "Evidence"],
                ["Lexer", "Completed", "src/lexer.py + tests"],
                ["Parser / AST", "Completed", "src/parser.py, ast_nodes.py"],
                ["Semantic / Symbol Table", "Completed", "src/semantic.py, symbol_table.py"],
                ["TAC / Optimization", "Completed", "src/tac.py, tac_opt.py"],
                ["Virtual Machine", "Completed", "src/interpreter.py"],
                ["Security analysis", "Initial implementation", "src/security/"],
                ["Testing", "Completed", "55 passing tests"],
            ])
            pdf.add_paragraph("Overall progress: [TO BE CALCULATED FROM ACTUAL MODULE STATUS]")
        elif number == "17":
            pdf.add_table([
                ["Concept", "Project implementation"],
                ["Lexical analysis", "Location-aware Lexer"],
                ["Syntax analysis", "Recursive-descent Parser"],
                ["AST", "Typed AST node classes"],
                ["Semantic analysis", "SemanticAnalyzer"],
                ["Symbol table", "Nested Scope and SymbolTable"],
                ["Intermediate code", "TACInstruction quadruples"],
                ["Optimization", "Folding, propagation, identities, DCE"],
                ["Execution", "Linear TAC Interpreter"],
            ])
        elif number == "18":
            pdf.add_code_block(
                "1. ./sudarshan examples/valid.mini --tokens\n"
                "2. ./sudarshan examples/valid.mini --ast\n"
                "3. ./sudarshan examples/valid.mini --symtab\n"
                "4. ./sudarshan examples/valid.mini --tac --opt\n"
                "5. ./sudarshan examples/valid.mini\n"
                "6. ./sudarshan examples/valid.mini --secure --security-report"
            )
            pdf.add_placeholder("INSERT TOKEN / AST / SYMBOL TABLE / TAC SCREENSHOTS")
        elif number == "19":
            pdf.add_table([
                ["Review criterion", "Marks", "Evidence"],
                ["Implementation Progress", "7", "Integrated compiler modules"],
                ["Technical Correctness", "5", "Execution and error tests"],
                ["Compiler Concept Application", "4", "Lexer through VM"],
                ["Code Quality", "3", "Modular source and tests"],
                ["Testing", "3", "55 passing tests"],
                ["Individual Understanding", "3", "Module explanations and viva"],
                ["TOTAL", "25", "Review 2 evaluation"],
            ])
        elif number == "20":
            questions = [
                ("What is lexical analysis?", "It converts source characters into tokens and reports invalid characters."),
                ("Why recursive descent?", "It maps grammar productions directly to readable parser functions."),
                ("What is an AST?", "A structural representation used by later compiler phases."),
                ("What does semantic analysis check?", "Declaration, scope, type, and expression validity."),
                ("What is TAC?", "A simple instruction-level IR with at most two operands per operation."),
                ("Why use temporaries?", "They make expression evaluation and later optimization explicit."),
                ("What is constant folding?", "Compile-time evaluation of operations whose operands are known constants."),
                ("How does the VM branch?", "It resolves LABEL targets through a precomputed label map."),
                ("How are scopes represented?", "Nested Scope objects use parent links and lookup."),
                ("How was correctness tested?", "Unit and integration tests cover each major pipeline stage."),
                ("What is the security layer?", "An opt-in derived TAC analysis, policy, integrity, and verification boundary."),
                ("What remains future work?", "Real semantics-preserving transformations and runtime profiling."),
            ]
            pdf.add_table([["Question", "Answer"]] + [[question, answer] for question, answer in questions])
        elif number == "A":
            pdf.add_code_block(
                "src/\n"
                "  lexer.py, parser.py, ast_nodes.py\n"
                "  semantic.py, symbol_table.py\n"
                "  tac.py, tac_opt.py, interpreter.py, main.py\n"
                "  security/ (CFG, features, scoring, policy, integrity, VM)\n"
                "tests/\n"
                "examples/\n"
                "docs/\n"
                "sudarshan, sudarshan.bat, pyproject.toml"
            )
        elif number == "B":
            for label in [
                "INSERT PROJECT STRUCTURE SCREENSHOT",
                "INSERT LEXER / TOKEN OUTPUT SCREENSHOT",
                "INSERT PARSER / AST SCREENSHOT",
                "INSERT SYMBOL TABLE SCREENSHOT",
                "INSERT TAC / OPTIMIZATION SCREENSHOT",
                "INSERT VM EXECUTION SCREENSHOT",
                "INSERT TEST RESULTS SCREENSHOT",
            ]:
                pdf.add_placeholder(label)
        elif number == "C":
            pdf.add_table([
                ["File", "Role"],
                ["src/lexer.py", "Lexer and token model"],
                ["src/parser.py", "Recursive-descent parser"],
                ["src/ast_nodes.py", "AST nodes and visualization"],
                ["src/semantic.py", "Semantic analysis"],
                ["src/symbol_table.py", "Scoped symbols"],
                ["src/tac.py", "TAC generation and formatting"],
                ["src/tac_opt.py", "TAC optimization"],
                ["src/interpreter.py", "Virtual machine"],
                ["src/security/", "Security analysis and verification"],
                ["tests/", "Unit and integration tests"],
            ])
    return pages


def main() -> None:
    first_pass = ReportPDF(str(OUTPUT))
    pages = build_report(first_pass)
    second_pass = ReportPDF(str(OUTPUT))
    build_report(second_pass, pages)
    second_pass.save()


if __name__ == "__main__":
    main()
