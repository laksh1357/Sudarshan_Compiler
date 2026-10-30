# Sudarshan Compiler — Advanced Compiler Engineering Architecture

This document specifies the advanced compiler engineering subsystem integrated into the Sudarshan Compiler pipeline, extending the 5-phase foundation with production-grade control flow, static single assignment, data flow analysis, loop optimizations, and differential verification.

---

## 1. Overview of the Advanced Subsystem

```
                         Sudarshan Source Code
                                   │
                                   ▼
                        Lexer & Parser (AST)
                                   │
                                   ▼
                           Semantic Analyzer
                                   │
                                   ▼
                        TAC Generator (Linear IR)
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        ▼                                                     ▼
┌───────────────────────┐                             ┌───────────────────────┐
│ Control Flow Graph    │                             │ Data Flow Framework   │
│ - Basic Blocks        │                             │ - Live Variables      │
│ - Dominator Tree      │                             │ - Reaching Defs       │
│ - Dominance Frontiers │                             │ - Work-list Iterators │
│ - Natural Loops       │                             └───────────────────────┘
└───────────┬───────────┘                                         │
            ▼                                                     │
┌───────────────────────┐                                         │
│ Static Single         │                                         │
│ Assignment (SSA) Form │                                         │
│ - Cytron DF+ Phis     │                                         │
│ - Versioned Renaming  │                                         │
│ - SSA Lowering        │                                         │
└───────────┬───────────┘                                         │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │ Advanced Optimization Engine  │
                       │ - CSE (Local & Commutative)   │
                       │ - Copy Propagation           │
                       │ - Loop Invariant Motion (LICM)│
                       │ - Strength Reduction (Loops)  │
                       │ - Algebraic Simplification    │
                       └───────────────┬───────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │ Optimization Pass Manager     │
                       │ - O0 (Baseline Analysis)      │
                       │ - O1 (Algebraic + CopyProp)   │
                       │ - O2 (O1 + CSE Sweeps)        │
                       │ - O3 (O2 + LICM + SR Sweeps)  │
                       └───────────────┬───────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │ Differential Testing Engine   │
                       │ Verified VM Execution         │
                       └───────────────────────────────┘
```

---

## 2. Phase 1: Control Flow Graph (CFG) Construction & Analysis (`src/analysis/cfg_advanced.py`)

### 2.1 Basic Block Partitioning
A Basic Block is a maximal straight-line sequence of instructions entered only at the first instruction and exited only at the last. Leaders are identified deterministically:
1. Instruction 0 (program entry).
2. Any instruction targeted by a conditional or unconditional branch (`LABEL` instructions).
3. Any instruction immediately succeeding a branch (`JUMP`, `JUMP_IF_FALSE`).

### 2.2 Dominator Tree Algorithm
Computes the immediate dominator ($\text{idom}$) for each block using the iterative reverse-postorder (RPO) intersection algorithm (Cooper, Harvey, Kennedy 2001):
$$\text{idom}(b) = \bigcap_{p \in \text{preds}(b),\, \text{processed}(p)} p$$
Full dominator sets $\text{Dom}(b)$ are computed efficiently by traversing the dominator tree upwards to the entry block.

### 2.3 Dominance Frontier Computation
For each join block $j$ with $|\text{preds}(j)| \ge 2$:
$$\text{For each } p \in \text{preds}(j): \quad \text{runner} \leftarrow p; \quad \text{while } \text{runner} \ne \text{idom}(j): \quad \text{DF}(\text{runner}) \leftarrow \text{DF}(\text{runner}) \cup \{j\}; \quad \text{runner} \leftarrow \text{idom}(\text{runner})$$

### 2.4 Natural Loop Detection & Back-Edge Analysis
A back edge is any control flow edge $t \to h$ where the target $h$ dominates the source $t$:
$$h \in \text{Dom}(t)$$
- **Header**: Block $h$.
- **Tail**: Block $t$.
- **Loop Body**: Set of all blocks that can reach $t$ without traversing $h$.
- **Loop Depth**: Monotonically tracked nesting level per block.

### 2.5 Visualization & Summary
- `cfg_to_dot(cfg)`: Generates compliant Graphviz DOT strings styling headers in steel-blue, back-edges with dashed red arrows, and depth annotations.
- `cfg_summary(cfg)`: Textual report reporting block counts, edges, loops, and variable statistics.

---

## 3. Phase 2: Static Single Assignment (SSA) Transformation (`src/analysis/ssa.py`)

### 3.1 Phi-Node Placement (Cytron et al. 1991)
Phi nodes ($\phi$) are placed at the iterated dominance frontiers:
$$\text{DF}^+(\text{defs}(v))$$
We implement **Semi-Pruned SSA** (Briggs et al.): variables defined in at most one basic block cannot have multiple reaching definitions and are excluded from $\phi$-placement, preventing unnecessary temporaries.

### 3.2 Renaming via Dominator Tree DFS
A stack-based walk over the dominator tree renames each definition of variable $v$ to $v.k$ ($k \in \mathbb{N}$) and substitutes current top-of-stack versions for operands. Phi node arguments in successor blocks are populated based on the incoming predecessor edge.

### 3.3 SSA Lowering (`ssa_to_tac`)
Lowers SSA back to standard Three-Address Code executable by the Sudarshan Virtual Machine:
1. Converts $\phi$-arguments into parallel copy assignments `ASSIGN(src, dst)` placed in the corresponding predecessor blocks immediately prior to terminating jumps.
2. Removes redundant self-copies ($x = x$).
3. De-versions variables back to canonical identifiers.

---

## 4. Phase 3: Data Flow Analysis (`src/analysis/dataflow.py`)

### 4.1 Live Variable Analysis (Backward, Union)
Calculates variables whose current values may be read before being overwritten on some execution path:
$$\text{LiveOut}(B) = \bigcup_{S \in \text{succ}(B)} \text{LiveIn}(S)$$
$$\text{LiveIn}(B) = \text{USE}(B) \cup (\text{LiveOut}(B) \setminus \text{DEF}(B))$$
Implemented using a work-list algorithm iterating backwards until convergence.

### 4.2 Reaching Definitions Analysis (Forward, Union)
Determines which variable definition sites $(v, \text{block}, \text{idx})$ reach the entry and exit of each basic block:
$$\text{ReachIn}(B) = \bigcup_{P \in \text{pred}(B)} \text{ReachOut}(P)$$
$$\text{ReachOut}(B) = \text{GEN}(B) \cup (\text{ReachIn}(B) \setminus \text{KILL}(B))$$

---

## 5. Phase 4: Advanced Optimization Engine (`src/advanced_optimizer.py`)

### 5.1 Common Subexpression Elimination (CSE)
Maintains an available expressions table $E = (\text{op}, a_1, a_2) \mapsto t$ within each basic block. Commutative operators (`ADD`, `MUL`, `EQ`, `NE`) are canonicalized ($a_1 \le a_2$). When an expression in $E$ is encountered, it is replaced with an `ASSIGN` from the previously computed temporary. Expressions are invalidated when their constituent variables are redefined.

### 5.2 Copy Propagation
Tracks copy assignments $t = x$ and substitutes uses of $t$ with $x$ as long as neither $t$ nor $x$ is redefined. Invalidated across control-flow boundaries.

### 5.3 Loop Invariant Code Motion (LICM)
Identifies arithmetic instructions within natural loop bodies whose operands are loop-invariant (defined strictly outside the loop body or numeric literals). Hoists loop-invariant instructions into the loop's pre-header block before the loop entry jump.

### 5.4 Strength Reduction
Targets expensive operations in loop bodies:
- Replaces multiplication by 2 with addition ($x \times 2 \to x + x$).

### 5.5 Algebraic Simplification
Evaluates algebraic identities directly:
- $x + 0 \to x$, $0 + x \to x$
- $x - 0 \to x$, $x - x \to 0$
- $x \times 0 \to 0$, $0 \times x \to 0$
- $x \times 1 \to x$, $1 \times x \to x$
- $x / 1 \to x$
- $x == x \to 1$, $x \ne x \to 0$

---

## 6. Phase 5: Optimization Pass Manager

Provides configurable pipeline execution via `OptimizationPassManager`:

| Level | Passes Executed | Description |
|---|---|---|
| **O0** | None | Raw IR baseline for analysis and debugging |
| **O1** | Algebraic, Copy Propagation | Lightweight single-instruction and copy simplifications |
| **O2** | Algebraic, CSE, Copy Propagation, Algebraic | Redundancy elimination and expression reuse |
| **O3** | Algebraic, CSE, Copy Propagation, LICM, Strength Reduction, Cleanups | Full loop optimization and iterative convergence |

---

## 7. Phase 6: Differential Testing (`src/differential_testing.py`)

Differential testing verifies semantics preservation across all optimization levels by compiling programs to TAC, running both the unoptimized reference TAC and the optimized TAC through the virtual machine, and validating that execution outputs are identical:
$$\text{Output}(\text{VM}(\text{RawTAC})) \equiv \text{Output}(\text{VM}(\text{OptTAC}_{O_k})) \quad \forall k \in \{0, 1, 2, 3\}$$

---

## 8. Verification & Test Suite

The test suite contains 226 unit and integration tests across 16 test modules:
- `tests/test_cfg_advanced.py`: 33 tests
- `tests/test_ssa.py`: 16 tests
- `tests/test_dataflow.py`: 22 tests
- `tests/test_advanced_optimizer.py`: 41 tests
- `tests/test_differential_testing.py`: 19 tests
- `tests/test_ast_viz.py`: 4 tests
- `tests/test_cli.py`: 9 tests
- `tests/test_errors.py`: 4 tests
- `tests/test_interpreter.py`: 8 tests
- `tests/test_lexer.py`: 4 tests
- `tests/test_optimizer.py`: 4 tests
- `tests/test_parser.py`: 5 tests
- `tests/test_security.py`: 10 tests
- `tests/test_semantic.py`: 5 tests
- `tests/test_tac.py`: 2 tests
- `backend/tests/`: 40 tests (API endpoints, Auth, DB, Multi-language)
