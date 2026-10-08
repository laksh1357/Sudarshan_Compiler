"""
Initial security subsystem for the Sudarshan compiler.

The subsystem is intentionally identity-only at this stage. It provides the
configuration and pass boundaries needed for future security transformations
without changing the existing compiler IR or execution semantics.
"""

from .config import SecurityConfig
from .security_pass import SecurityPass
from .cfg import BasicBlock, ControlFlowGraph, build_cfg
from .features import SecurityFeatures, analyze_block
from .policy import ProtectionLevel, SecurityPolicy, select_policy
from .protected_ir import ProtectedProgram
from errors import SecurityIntegrityError
from .report import format_report
from .scoring import SecurityRiskLevel, SecurityScore, score_features
from .secure_vm import SecureInterpreter
from .transform import (
    IdentityTransformation,
    SecurityContext,
    SecurityTransformation,
    TransformationDiagnostics,
    protect_ir,
)

__all__ = [
    "SecurityConfig",
    "SecurityPass",
    "BasicBlock",
    "ControlFlowGraph",
    "build_cfg",
    "SecurityFeatures",
    "analyze_block",
    "ProtectionLevel",
    "SecurityPolicy",
    "select_policy",
    "ProtectedProgram",
    "SecurityIntegrityError",
    "format_report",
    "SecurityRiskLevel",
    "SecurityScore",
    "score_features",
    "SecureInterpreter",
    "protect_ir",
    "IdentityTransformation",
    "SecurityContext",
    "SecurityTransformation",
    "TransformationDiagnostics",
]
