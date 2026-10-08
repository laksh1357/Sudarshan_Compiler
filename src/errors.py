"""
Centralized Error Handling Module for Sudarshan Compiler.

Defines a clean hierarchy of compiler exceptions with line, column,
and optional source code context tracking across all pipeline phases.
"""

from typing import Optional


class SudarshanError(Exception):
    """Base class for all Sudarshan compiler and interpreter errors."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        source_context: Optional[str] = None
    ):
        self.message = message
        self.line = line
        self.column = column
        self.source_context = source_context
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        error_name = self.__class__.__name__
        location_str = ""

        if self.line is not None and self.column is not None:
            location_str = f" at line {self.line}, column {self.column}"
        elif self.line is not None:
            location_str = f" at line {self.line}"

        base_msg = f"{error_name}: {self.message}{location_str}"

        if self.source_context:
            base_msg += f"\n  Context: {self.source_context.strip()}"

        return base_msg


# Base Aliases for backward compatibility
MiniLangError = SudarshanError
CompilerError = SudarshanError


class LexerError(SudarshanError):
    """Raised when an unrecognized character or malformed token is scanned."""
    pass


class ParserError(SudarshanError):
    """Raised when source tokens violate Sudarshan syntax/grammar rules."""
    pass


class SemanticError(SudarshanError):
    """Raised on scope violations, undeclared variables, or type mismatches."""
    pass


class TACError(SudarshanError):
    """Raised during intermediate code generation or IR optimization."""
    pass


class CompilerRuntimeError(SudarshanError):
    """Raised during TAC execution (e.g. division by zero, undefined access)."""
    pass


class SecurityIntegrityError(SudarshanError):
    """Raised when protected IR or its metadata fails integrity validation."""
    pass
