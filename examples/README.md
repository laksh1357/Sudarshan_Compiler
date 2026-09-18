# Sudarshan Example Source Files (`.mini`)

This directory contains sample source files written in the **Sudarshan** imperative programming language. Each file demonstrates specific language capabilities or error-handling features of the compiler.

## Example File Index

| File | Description | Target Compiler Feature |
|---|---|---|
| [`valid.mini`](valid.mini) | Full language feature test (while loop, nested if/else, scope resolution, arithmetic) | Valid End-to-End Execution |
| [`opt_test.mini`](opt_test.mini) | Compile-time constant arithmetic and unreachable conditional branch demo | Constant Folding & DCE (`--opt`) |
| [`nested_scope.mini`](nested_scope.mini) | Nested block scoping, variable shadowing (`int x = 10; { int x = 20; }`) | Semantic Analysis & Scope Mangling |
| [`error_syntax.mini`](error_syntax.mini) | Missing semicolon syntax error test case | Parser Syntax Exception Handling |
| [`error_semantic.mini`](error_semantic.mini) | Redeclaration of variable in same scope / undeclared access | Semantic Exception Handling |
| [`error_lexical.mini`](error_lexical.mini) | Unrecognized character symbol test case | Lexer Exception Handling |
| [`error_runtime.mini`](error_runtime.mini) | Division-by-zero expression test case | VM Runtime Exception Handling |

## Running Examples

Execute any example file using the Sudarshan launcher:

```bash
# Standard execution
./sudarshan examples/valid.mini

# Inspect all compiler pipeline stages
./sudarshan examples/opt_test.mini --all

# View phase-by-phase educational explanation
./sudarshan examples/nested_scope.mini --explain
```
