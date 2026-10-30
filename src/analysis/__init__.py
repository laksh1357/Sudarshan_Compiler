"""
Advanced Compiler Analysis Subsystem for Sudarshan Compiler.

Provides:
  - Control Flow Graph (CFG) with dominator tree, loop detection, and Graphviz DOT export
  - Static Single Assignment (SSA) form with correct Phi node insertion
  - Data Flow Analysis: Live Variable Analysis and Reaching Definitions
"""

from .cfg_advanced import (
    BasicBlock,
    ControlFlowGraph,
    build_cfg,
    cfg_to_dot,
    cfg_summary,
)
from .ssa import (
    PhiNode,
    SSAVariable,
    SSAInstruction,
    SSABlock,
    SSAProgram,
    build_ssa,
    ssa_to_tac,
)
from .dataflow import (
    LiveVariableAnalysis,
    ReachingDefinitionsAnalysis,
    DataFlowResult,
    liveness_result,
    reaching_defs_result,
)

__all__ = [
    # CFG
    "BasicBlock",
    "ControlFlowGraph",
    "build_cfg",
    "cfg_to_dot",
    "cfg_summary",
    # SSA
    "PhiNode",
    "SSAVariable",
    "SSAInstruction",
    "SSABlock",
    "SSAProgram",
    "build_ssa",
    "ssa_to_tac",
    # Data Flow
    "LiveVariableAnalysis",
    "ReachingDefinitionsAnalysis",
    "DataFlowResult",
    "liveness_result",
    "reaching_defs_result",
]
