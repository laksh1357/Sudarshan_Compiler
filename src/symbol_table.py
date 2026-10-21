"""
Symbol Table Module for Sudarshan Compiler.

Implements a lexically-scoped Symbol Table supporting nested scopes, block entry/exit,
variable declaration checks, parent scope resolution, and shadowing.
"""

from typing import Dict, Optional
from errors import CompilerRuntimeError


class Symbol:
    """Represents a declared symbol (variable) in Sudarshan."""

    def __init__(
        self,
        name: str,
        type_name: str = "int",
        line: Optional[int] = None,
        column: Optional[int] = None,
        scope_level: int = 0
    ):
        self.name = name
        self.type_name = type_name
        self.line = line
        self.column = column
        self.scope_level = scope_level

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type_name": self.type_name,
            "line": self.line,
            "column": self.column,
            "scope_level": self.scope_level,
        }

    def __repr__(self) -> str:
        loc = f" (L{self.line}:C{self.column})" if self.line is not None else ""
        return f"Symbol({self.name}: {self.type_name}, Scope {self.scope_level}{loc})"


class Scope:
    """Represents a single lexical scope environment."""

    def __init__(self, scope_level: int = 0, parent: Optional["Scope"] = None):
        self.scope_level = scope_level
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}
        self.children: list = []

    def declare(self, symbol: Symbol) -> Symbol:
        """Declares a symbol in the current scope. Raises ValueError if already declared in this scope."""
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]
            loc = f" at line {existing.line}" if existing.line else ""
            raise ValueError(f"Variable '{symbol.name}' is already declared in the current scope{loc}.")
        self.symbols[symbol.name] = symbol
        return symbol

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Looks up a symbol ONLY in this current scope (for duplicate detection / shadowing)."""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Recursively looks up a symbol in this scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def dump(self, indent: int = 0) -> str:
        """Returns a string representation of this scope and its symbols."""
        prefix = "  " * indent
        res = f"{prefix}=== Scope Level {self.scope_level} ===\n"
        if not self.symbols:
            res += f"{prefix}  (empty)\n"
        else:
            for name, sym in self.symbols.items():
                res += f"{prefix}  {sym}\n"
        return res

    def to_dict(self) -> dict:
        return {
            "scope_level": self.scope_level,
            "symbols": [s.to_dict() for s in self.symbols.values()],
        }


class SymbolTable:
    """
    Manages active lexical scopes during semantic analysis.
    Supports enter_scope(), exit_scope(), declare(), and lookup().
    """

    def __init__(self):
        self.global_scope = Scope(scope_level=0, parent=None)
        self._current_scope = self.global_scope
        self.all_scopes: list[Scope] = [self.global_scope]

    def current_scope(self) -> Scope:
        """Returns the active scope."""
        return self._current_scope

    def enter_scope(self) -> Scope:
        """Enters a new nested scope (e.g. entering a block { ... })."""
        new_scope = Scope(scope_level=self._current_scope.scope_level + 1, parent=self._current_scope)
        self._current_scope.children.append(new_scope)
        self._current_scope = new_scope
        self.all_scopes.append(new_scope)
        return new_scope

    def exit_scope(self) -> Scope:
        """Exits the current nested scope, returning to its parent scope."""
        if self._current_scope.parent is None:
            raise CompilerRuntimeError("Cannot exit global scope.")
        self._current_scope = self._current_scope.parent
        return self._current_scope

    def declare(
        self,
        name: str,
        type_name: str = "int",
        line: Optional[int] = None,
        column: Optional[int] = None
    ) -> Symbol:
        """Declares a symbol in the current active scope."""
        sym = Symbol(
            name=name,
            type_name=type_name,
            line=line,
            column=column,
            scope_level=self._current_scope.scope_level
        )
        return self._current_scope.declare(sym)

    def lookup(self, name: str) -> Optional[Symbol]:
        """Looks up a symbol recursively starting from current scope up to global scope."""
        return self._current_scope.lookup(name)

    def lookup_current_scope(self, name: str) -> Optional[Symbol]:
        """Looks up a symbol strictly in the current active scope."""
        return self._current_scope.lookup_current_scope(name)

    def dump(self) -> str:
        """Dumps the global scope table and nested scopes."""
        res = []
        for scope in self.all_scopes:
            res.append(scope.dump())
        return "\n".join(res)

    def to_dict(self) -> dict:
        """Exports all scopes and symbols in a structured format."""
        all_symbols = []
        for scope in self.all_scopes:
            for sym in scope.symbols.values():
                all_symbols.append(sym.to_dict())
        return {
            "scopes": [s.to_dict() for s in self.all_scopes],
            "symbols": all_symbols,
        }

