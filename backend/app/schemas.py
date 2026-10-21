"""
Pydantic Schemas for Sudarshan Compiler Studio API.
"""

from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class TokenModel(BaseModel):
    type: str
    value: Any
    line: int
    column: int


class ASTNodeModel(BaseModel):
    id: str
    type: str
    label: str
    line: Optional[int] = None
    column: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    relation: Optional[str] = None
    children: List["ASTNodeModel"] = Field(default_factory=list)


class SymbolModel(BaseModel):
    name: str
    type_name: str = "int"
    line: Optional[int] = None
    column: Optional[int] = None
    scope_level: int = 0


class ScopeModel(BaseModel):
    scope_level: int
    symbols: List[SymbolModel] = Field(default_factory=list)


class SymbolTableModel(BaseModel):
    scopes: List[ScopeModel] = Field(default_factory=list)
    symbols: List[SymbolModel] = Field(default_factory=list)


class SemanticDiagnosticModel(BaseModel):
    severity: str = "info"  # "info" | "warning" | "error"
    message: str
    line: Optional[int] = None
    column: Optional[int] = None


class TACInstructionModel(BaseModel):
    index: int
    op: str
    arg1: Any = None
    arg2: Any = None
    result: Any = None
    text: str


class OptimizationRecordModel(BaseModel):
    pass_name: str
    original: str
    transformed: str
    reason: str
    category: str


class OptimizationStatsModel(BaseModel):
    original_count: int
    optimized_count: int
    reduction_percentage: float
    transformations_count: int


class CompilerErrorModel(BaseModel):
    phase: str
    error_type: str
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    source_context: Optional[str] = None


class TimingModel(BaseModel):
    lexical_ms: float = 0.0
    syntax_ms: float = 0.0
    semantic_ms: float = 0.0
    tac_ms: float = 0.0
    optimization_ms: float = 0.0
    execution_ms: float = 0.0
    total_ms: float = 0.0


class CompileRequest(BaseModel):
    source_code: str = Field(..., max_length=65536, description="Sudarshan source code (max 64KB)")
    optimize: bool = Field(default=True, description="Enable TAC optimization passes")
    max_steps: int = Field(default=100000, ge=1, le=1000000, description="Virtual Machine step execution limit")


class CompileRunRequest(BaseModel):
    source_code: str = Field(..., max_length=65536, description="Sudarshan source code (max 64KB)")
    optimize: bool = Field(default=True, description="Enable TAC optimization passes")
    max_steps: int = Field(default=100000, ge=1, le=1000000, description="Virtual Machine step execution limit")


class RunRequest(BaseModel):
    source_code: Optional[str] = Field(default=None, max_length=65536)
    max_steps: int = Field(default=100000, ge=1, le=1000000)


class CompilationResponse(BaseModel):
    success: bool
    failed_phase: Optional[str] = None
    tokens: Optional[List[TokenModel]] = None
    ast: Optional[Dict[str, Any]] = None
    ast_text: Optional[str] = None
    ast_dot: Optional[str] = None
    symbol_table: Optional[SymbolTableModel] = None
    semantic_diagnostics: List[SemanticDiagnosticModel] = Field(default_factory=list)
    raw_tac: Optional[List[TACInstructionModel]] = None
    raw_tac_text: Optional[str] = None
    optimized_tac: Optional[List[TACInstructionModel]] = None
    optimized_tac_text: Optional[str] = None
    optimization_report: List[OptimizationRecordModel] = Field(default_factory=list)
    optimization_stats: Optional[OptimizationStatsModel] = None
    compilation_errors: List[CompilerErrorModel] = Field(default_factory=list)
    timing: TimingModel = Field(default_factory=TimingModel)

    # Execution fields (populated for compile-run and run)
    execution_status: Optional[str] = None  # "success" | "error" | "step_limit_exceeded" | None
    program_output: Optional[List[int]] = None
    stdout_text: Optional[str] = None
    runtime_errors: List[CompilerErrorModel] = Field(default_factory=list)
    execution_steps: Optional[int] = None


class ExampleItem(BaseModel):
    id: str
    name: str
    category: str
    description: str
    filename: str
    source_code: str
    expected_output: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    name: str = "Sudarshan Compiler Studio"
    version: str = "1.0.0"
    compiler: str = "Sudarshan (MiniLang)"
    supported_phases: List[str]
