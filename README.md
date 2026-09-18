# Sudarshan — An End-to-End Compiler and Virtual Machine

[![Compiler Design Laboratory](https://img.shields.io/badge/Course-Compiler_Design_Laboratory-1B365D?style=for-the-badge)](https://github.com/laksh1357/MyOWN_Compiler)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/Tests-45%20Passed-success?style=for-the-badge)](tests/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**Compiler Design Laboratory Individual Project**  
**Student Name**: Lakshya Singh | **Reg No.**: 24BDS0054  
**Project Title**: Sudarshan: An End-to-End Compiler and Virtual Machine  
**GitHub Repository**: [https://github.com/laksh1357/MyOWN_Compiler](https://github.com/laksh1357/MyOWN_Compiler)

---

## 1. Project Overview

**Sudarshan** is an imperative programming language and an end-to-end compiler pipeline implemented in pure Python 3.

The project implements all classic compiler construction phases:
- **Lexical Analysis**: DFA scanner & location-aware tokenizer ([`src/lexer.py`](src/lexer.py))
- **Syntax Analysis**: LL(1) recursive descent parser & AST visualizer ([`src/parser.py`](src/parser.py), [`src/ast_nodes.py`](src/ast_nodes.py))
- **Semantic Analysis**: Lexical block scope & symbol table validator ([`src/semantic.py`](src/semantic.py), [`src/symbol_table.py`](src/symbol_table.py))
- **Intermediate Code Generation**: Three-Address Code (TAC) quadruples with register allocation ([`src/tac.py`](src/tac.py))
- **Intermediate Code Optimization**: Multi-pass constant folding, constant propagation & dead code elimination ([`src/tac_opt.py`](src/tac_opt.py))
- **Virtual Machine Execution**: Linear TAC quadruples interpreter & runtime VM ([`src/interpreter.py`](src/interpreter.py))

Designed specifically for Compiler Design Laboratory evaluation, the codebase is fully modular, cross-platform, zero-dependency, type-hinted, and presentation-ready.

---

## 2. Key Features & Technical Innovations

1. **Multi-Pass Constant Folding & Propagation**: Evaluates complex compile-time arithmetic (`2 + 3 * 4` $\rightarrow$ `14`) and comparison expressions dynamically before Virtual Machine execution while safely preserving division-by-zero operations for runtime error handling.
2. **Static Branch Pruning & Dead Code Elimination**: Converts constant conditional jumps (`IF_FALSE 0 GOTO L1` $\rightarrow$ `JUMP L1`) and removes unreachable quadruples following unconditional `GOTO` jumps across basic blocks.
3. **Scope Name Mangling for Register Isolation**: Resolves variable shadowing in flat register-based Three-Address Code by appending scope depth suffixes (`x_s1`), preserving lexical block isolation without complex stack frame overhead.
4. **AST ASCII & Graphical Visualization**: Generates clean hierarchical ASCII tree visualizations directly in terminal (`dump_ast`), and optional Graphviz image export (`render_ast_graph`) routed to a clean `output/` directory with automatic fallback handling.
5. **Cross-Platform Portable Entry Points**: Invokable seamlessly via `./sudarshan` (Linux/macOS executable) or `sudarshan.bat` (Windows CMD/PowerShell), using standard `pathlib.Path` resolution.
6. **Zero-Dependency 100% Handwritten Architecture**: Fully handwritten scanner, parser, symbol table manager, TAC IR generator, optimizer pass, and VM interpreter built strictly with Python standard library.
7. **Interactive Educational CLI Explainer (`--explain`)**: Built-in CLI flag providing step-by-step educational analysis showing transformation metrics across all 5 compiler phases.

---

## 3. Project Directory Structure

```text
MyOWN_Compiler/
├── src/                          # Phase-by-phase Compiler Source Code
│   ├── __init__.py
│   ├── errors.py                 # Centralized exception hierarchy (SudarshanError)
│   ├── lexer.py                  # Phase 1: Scanner & Tokenizer
│   ├── ast_nodes.py              # Phase 2: AST Node definitions & visualizer
│   ├── parser.py                 # Phase 2: LL(1) Recursive Descent Parser
│   ├── symbol_table.py           # Phase 3: Lexically-scoped Symbol Table
│   ├── semantic.py               # Phase 3: Static Semantic Analyzer
│   ├── tac.py                    # Phase 4: Three-Address Code Generator
│   ├── tac_opt.py                # Phase 4b: TAC Constant Folding & DCE Optimizer
│   ├── interpreter.py            # Phase 5: Virtual Machine Interpreter
│   └── main.py                   # Central CLI Driver & Entry Point
├── tests/                        # Comprehensive Automated Test Suite (45 Tests)
│   ├── test_lexer.py             # Lexer tokenization unit tests
│   ├── test_parser.py            # Parser grammar & precedence tests
│   ├── test_semantic.py          # Scope isolation & semantic validation tests
│   ├── test_tac.py               # TAC quadruple generation tests
│   ├── test_optimizer.py         # Algebraic identity, folding & DCE tests
│   ├── test_interpreter.py       # VM execution & runtime error tests
│   ├── test_errors.py            # Exception hierarchy & formatting tests
│   ├── test_ast_viz.py           # AST visualization & fallback tests
│   └── test_cli.py               # CLI driver & portability regression tests
├── examples/                     # Sudarshan Source Code Files (.mini)
│   ├── valid.mini                # Complete feature test (loops, scopes, arithmetic)
│   ├── opt_test.mini             # Constant folding & dead code elimination demo
│   ├── nested_scope.mini         # Lexical block scoping & variable shadowing
│   ├── error_syntax.mini         # Syntax error handling demonstration
│   ├── error_semantic.mini       # Scope & undeclared variable error test
│   ├── error_lexical.mini        # Unrecognized token error test
│   └── error_runtime.mini        # VM division-by-zero runtime error test
├── docs/                         # Project Reports & Document Generators
│   ├── generate_pdf.py           # Pure Python PDF generator engine
│   ├── generate_phase1_pdf.py    # Generator for Phase1_Report.pdf
│   ├── generate_review1_pdf.py   # Generator for Review1_Defense_Guide.pdf
│   ├── generate_docx.py          # Generator for Phase1_Project_Report.docx
│   ├── SUDARSHAN_Compiler_Documentation.pdf
│   ├── Phase1_Report.pdf
│   ├── Review1_Defense_Guide.pdf
│   └── Phase1_Project_Report.docx
├── output/                       # Generated build artifacts (e.g. AST graphs)
├── sudarshan                     # Cross-platform CLI launcher script (macOS/Linux)
├── sudarshan.bat                 # Windows CMD/PowerShell launcher script
├── gsd-pipeline.sh               # Integrated automated pipeline runner
├── pyproject.toml                # Modern Python package configuration & test settings
├── LICENSE                       # MIT License
└── README.md                     # Comprehensive project documentation
```

---

## 4. Compiler Pipeline Architecture

```text
                  Source Code (.mini)
                           │
                           ▼
Phase 1: Lexical Analyzer (src/lexer.py & src/errors.py) ──► Token Stream (Line & Col tracking)
                           │
                           ▼
Phase 2: Syntax Analyzer (src/parser.py & src/ast_nodes.py) ──► Abstract Syntax Tree (AST)
                           │
                           ▼
Phase 3: Semantic Analyzer (src/semantic.py & src/symbol_table.py) ──► Scoped Symbol Table
                           │
                           ▼
Phase 4: Intermediate Code Generator (src/tac.py) ──► Three-Address Code (Quadruples)
                           │
                           ▼
Phase 4b: TAC Optimizer Pass (src/tac_opt.py) ──► Constant Folding & DCE
                           │
                           ▼
Phase 5: Virtual Machine Interpreter (src/interpreter.py) ──► Code Execution & Output
```

---

## 5. Sudarshan Formal Grammar (BNF Syntax)

```ebnf
program    -> statement*
statement  -> varDecl | assign | printStmt | ifStmt | whileStmt | block
varDecl    -> 'int' ID '=' expr ';'
assign     -> ID '=' expr ';'
printStmt  -> 'print' '(' expr ')' ';'
ifStmt     -> 'if' '(' expr ')' block ('else' (ifStmt | block))?
whileStmt  -> 'while' '(' expr ')' block
block      -> '{' statement* '}'
expr       -> comparison
comparison -> addExpr (('==' | '!=' | '<' | '>' | '<=' | '>=') addExpr)*
addExpr    -> term (('+' | '-') term)*
term       -> factor (('*' | '/') factor)*
factor     -> NUMBER | ID | '(' expr ')' | '-' factor
```

---

## 6. How to Run & CLI Usage

### Quick Start
Execute the compiler using the portable `./sudarshan` launcher, `sudarshan.bat`, or `python3 src/main.py`:

```bash
# Run program execution
./sudarshan examples/valid.mini

# Display output across all compiler phases
./sudarshan examples/valid.mini --all

# Run educational phase-by-phase explanation
./sudarshan examples/valid.mini --explain

# Run complete automated test suite (45 tests)
python3 -m unittest discover -s tests
# or using pytest in virtual environment:
.venv/bin/python -m pytest -v
```

### Command Line Flags

| Flag | Description |
|---|---|
| `--tokens` | Display token stream generated by Lexer |
| `--ast` | Display parsed Abstract Syntax Tree ASCII representation |
| `--viz` | Render AST to graphical image (`output/ast_tree.png`) via Graphviz with fallback |
| `--symtab` | Display global & block-level Symbol Tables |
| `--tac` | Display unoptimized Three-Address Code quadruples |
| `--opt` | Display optimized Three-Address Code quadruples |
| `--explain` | Display detailed educational explanation of all compiler phases |
| `--all` | Display output from all compiler phases |
| `--debug` | Preserve full Python stack traces during execution for debugging |

---

## 7. License

This project is open-source under the [MIT License](LICENSE).
