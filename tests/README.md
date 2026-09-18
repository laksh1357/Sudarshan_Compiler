# Sudarshan Automated Test Suite

This directory contains the comprehensive automated test suite for the **Sudarshan** compiler, comprising **45 unit and integration tests** implemented with Python's standard `unittest` framework and compatible with `pytest`.

## Test Module Overview

| Test Module | Tests | Description |
|---|---|---|
| [`test_lexer.py`](test_lexer.py) | 4 | Valid token scanning, position tracking, comment stripping, lexical error detection |
| [`test_parser.py`](test_parser.py) | 5 | BNF grammar matching, operator precedence (`*`/`/` over `+`/`-`), block parsing, syntax errors |
| [`test_semantic.py`](test_semantic.py) | 5 | Symbol table verification, block scope isolation, variable shadowing, duplicate/undeclared errors |
| [`test_tac.py`](test_tac.py) | 2 | Quadruple IR generation, temporary allocation (`t1`, `t2`), label generation (`L1`, `L2`) |
| [`test_optimizer.py`](test_optimizer.py) | 4 | Multi-pass constant folding, algebraic identity simplification, safe division-by-zero guards, DCE |
| [`test_interpreter.py`](test_interpreter.py) | 8 | TAC execution, register state evaluation, division-by-zero runtime errors, custom exception isolation |
| [`test_errors.py`](test_errors.py) | 4 | Exception hierarchy polymorphic catching, line/column formatting, source context rendering |
| [`test_ast_viz.py`](test_ast_viz.py) | 4 | Graphviz dot rendering, output directory routing (`output/ast_tree.png`), missing binary fallback |
| [`test_cli.py`](test_cli.py) | 9 | CLI flag parsing (`--tokens`, `--ast`, `--viz`, `--opt`, `--explain`), portable relative path handling |

## Executing the Test Suite

Run using unittest standard discovery:
```bash
python3 -m unittest discover -s tests -v
```

Or using pytest in the project virtual environment:
```bash
.venv/bin/python -m pytest -v
```
