"""Security pass boundary for the Sudarshan compiler."""

from typing import TypeVar

from .config import SecurityConfig


IR = TypeVar("IR")


class SecurityPass:
    """Applies the optional security transformation to compiler IR.

    The initial implementation is deliberately an identity transformation.
    It establishes a stable pass boundary while preserving the existing IR
    object and all current compiler behavior.
    """

    def __init__(self, config: SecurityConfig):
        self.config = config

    def transform(self, ir: IR) -> IR:
        """Return the input IR unchanged until security transforms are added."""
        return ir
