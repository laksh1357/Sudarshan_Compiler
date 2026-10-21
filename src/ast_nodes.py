"""
Abstract Syntax Tree (AST) Nodes Module for Sudarshan Compiler.

Defines AST nodes for all Sudarshan constructs, preserving source location (line, column).
Includes a pretty-printer function dump_ast() for visual inspection during demonstrations.
"""

from typing import List, Optional


class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""

    def __init__(self, line: Optional[int] = None, column: Optional[int] = None):
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# --- Root Node ---

class Program(ASTNode):
    """Root AST node representing an entire Sudarshan program."""

    def __init__(self, statements: Optional[List[ASTNode]] = None, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.statements: List[ASTNode] = statements if statements is not None else []


# --- Expression Nodes ---

class IntegerLiteral(ASTNode):
    """AST node for integer literal values (e.g. 5, 42)."""

    def __init__(self, value: int, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.value = value


class Variable(ASTNode):
    """AST node for variable references (e.g. x, count)."""

    def __init__(self, name: str, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.name = name


class UnaryExpr(ASTNode):
    """AST node for unary expressions (e.g. -x)."""

    def __init__(self, operator: str, operand: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.operator = operator
        self.operand = operand


class BinaryExpr(ASTNode):
    """AST node for binary expressions (e.g. x + 1, a < b)."""

    def __init__(self, left: ASTNode, operator: str, right: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.left = left
        self.operator = operator
        self.right = right


# --- Statement Nodes ---

class VarDecl(ASTNode):
    """AST node for variable declarations (e.g. int x = 5;)."""

    def __init__(self, var_type: str, name: str, initializer: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.var_type = var_type
        self.name = name
        self.initializer = initializer


class Assignment(ASTNode):
    """AST node for variable assignments (e.g. x = y + 1;)."""

    def __init__(self, name: str, value: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.name = name
        self.value = value


class PrintStmt(ASTNode):
    """AST node for print statements (e.g. print(x);)."""

    def __init__(self, expression: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.expression = expression


class IfStmt(ASTNode):
    """AST node for conditional statements (if (cond) then_branch else else_branch)."""

    def __init__(self, condition: ASTNode, then_branch: ASTNode, else_branch: Optional[ASTNode] = None, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class WhileStmt(ASTNode):
    """AST node for loop statements (while (cond) body)."""

    def __init__(self, condition: ASTNode, body: ASTNode, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.condition = condition
        self.body = body


class Block(ASTNode):
    """AST node for block statements ({ statement* })."""

    def __init__(self, statements: Optional[List[ASTNode]] = None, line: Optional[int] = None, column: Optional[int] = None):
        super().__init__(line, column)
        self.statements: List[ASTNode] = statements if statements is not None else []


# --- AST Pretty Printer ---

def dump_ast(node: ASTNode, indent: int = 0) -> str:
    """
    Recursively formats an AST node hierarchy into a clean, human-readable string.
    Suitable for lab demonstrations and CLI --ast flag output.
    """
    prefix = "  " * indent

    if isinstance(node, Program):
        res = f"{prefix}Program:\n"
        for stmt in node.statements:
            res += dump_ast(stmt, indent + 1)
        return res

    elif isinstance(node, VarDecl):
        res = f"{prefix}VarDecl ({node.var_type} {node.name}):\n"
        res += dump_ast(node.initializer, indent + 1)
        return res

    elif isinstance(node, Assignment):
        res = f"{prefix}Assignment ({node.name} =):\n"
        res += dump_ast(node.value, indent + 1)
        return res

    elif isinstance(node, PrintStmt):
        res = f"{prefix}PrintStmt:\n"
        res += dump_ast(node.expression, indent + 1)
        return res

    elif isinstance(node, IfStmt):
        res = f"{prefix}IfStmt:\n"
        res += f"{prefix}  Condition:\n" + dump_ast(node.condition, indent + 2)
        res += f"{prefix}  Then:\n" + dump_ast(node.then_branch, indent + 2)
        if node.else_branch:
            res += f"{prefix}  Else:\n" + dump_ast(node.else_branch, indent + 2)
        return res

    elif isinstance(node, WhileStmt):
        res = f"{prefix}WhileStmt:\n"
        res += f"{prefix}  Condition:\n" + dump_ast(node.condition, indent + 2)
        res += f"{prefix}  Body:\n" + dump_ast(node.body, indent + 2)
        return res

    elif isinstance(node, Block):
        res = f"{prefix}Block:\n"
        for stmt in node.statements:
            res += dump_ast(stmt, indent + 1)
        return res

    elif isinstance(node, BinaryExpr):
        res = f"{prefix}BinaryExpr ('{node.operator}'):\n"
        res += dump_ast(node.left, indent + 1)
        res += dump_ast(node.right, indent + 1)
        return res

    elif isinstance(node, UnaryExpr):
        res = f"{prefix}UnaryExpr ('{node.operator}'):\n"
        res += dump_ast(node.operand, indent + 1)
        return res

    elif isinstance(node, IntegerLiteral):
        return f"{prefix}IntegerLiteral({node.value})\n"

    elif isinstance(node, Variable):
        return f"{prefix}Variable({node.name})\n"

    else:
        return f"{prefix}{node.__class__.__name__}\n"


# --- AST Graphviz Visualization (Optional Engine) ---

def export_ast_dot(node: ASTNode) -> str:
    """
    Generates Graphviz DOT syntax representation of the AST node tree.
    Pure python string formatting with zero external dependencies.
    """
    lines = ["digraph AST {", "  node [shape=box, style=filled, fillcolor=lightyellow, fontname=\"Courier\"];"]
    node_counter = 0

    def _visit(n: ASTNode) -> int:
        nonlocal node_counter
        curr_id = node_counter
        node_counter += 1

        label = n.__class__.__name__
        if isinstance(n, IntegerLiteral):
            label += f"({n.value})"
        elif isinstance(n, Variable):
            label += f"({n.name})"
        elif isinstance(n, VarDecl):
            label += f"({n.var_type} {n.name})"
        elif isinstance(n, (BinaryExpr, UnaryExpr)):
            label += f"('{n.operator}')"
        elif isinstance(n, Assignment):
            label += f"({n.name}=)"

        escaped_label = label.replace('"', '\\"')
        lines.append(f'  node_{curr_id} [label="{escaped_label}"];')

        children = []
        if isinstance(n, Program):
            children = n.statements
        elif isinstance(n, VarDecl):
            children = [n.initializer]
        elif isinstance(n, Assignment):
            children = [n.value]
        elif isinstance(n, PrintStmt):
            children = [n.expression]
        elif isinstance(n, IfStmt):
            children = [n.condition, n.then_branch] + ([n.else_branch] if n.else_branch else [])
        elif isinstance(n, WhileStmt):
            children = [n.condition, n.body]
        elif isinstance(n, Block):
            children = n.statements
        elif isinstance(n, BinaryExpr):
            children = [n.left, n.right]
        elif isinstance(n, UnaryExpr):
            children = [n.operand]

        for child in children:
            if child:
                child_id = _visit(child)
                lines.append(f"  node_{curr_id} -> node_{child_id};")

        return curr_id

    _visit(node)
    lines.append("}")
    return "\n".join(lines)


def ast_to_dict(node: ASTNode) -> dict:
    """
    Serializes an ASTNode tree into a structured dictionary suitable
    for JSON serialization and interactive graphical tree rendering.
    """
    node_id = 0

    def _serialize(n: ASTNode) -> dict:
        nonlocal node_id
        curr_id = f"ast_node_{node_id}"
        node_id += 1

        node_type = n.__class__.__name__
        label = node_type
        details = {}

        if isinstance(n, IntegerLiteral):
            label = f"Literal: {n.value}"
            details["value"] = n.value
        elif isinstance(n, Variable):
            label = f"Var: {n.name}"
            details["name"] = n.name
        elif isinstance(n, VarDecl):
            label = f"VarDecl: {n.var_type} {n.name}"
            details["var_type"] = n.var_type
            details["name"] = n.name
        elif isinstance(n, Assignment):
            label = f"Assign: {n.name} ="
            details["name"] = n.name
        elif isinstance(n, BinaryExpr):
            label = f"BinaryOp: {n.operator}"
            details["operator"] = n.operator
        elif isinstance(n, UnaryExpr):
            label = f"UnaryOp: {n.operator}"
            details["operator"] = n.operator
        elif isinstance(n, PrintStmt):
            label = "Print"
        elif isinstance(n, IfStmt):
            label = "If"
        elif isinstance(n, WhileStmt):
            label = "While"
        elif isinstance(n, Block):
            label = "Block"
        elif isinstance(n, Program):
            label = "Program"

        children_dict = []
        raw_children = []
        if isinstance(n, Program):
            raw_children = [("stmt", s) for s in n.statements]
        elif isinstance(n, VarDecl):
            raw_children = [("init", n.initializer)]
        elif isinstance(n, Assignment):
            raw_children = [("value", n.value)]
        elif isinstance(n, PrintStmt):
            raw_children = [("expr", n.expression)]
        elif isinstance(n, IfStmt):
            raw_children = [("condition", n.condition), ("then", n.then_branch)]
            if n.else_branch:
                raw_children.append(("else", n.else_branch))
        elif isinstance(n, WhileStmt):
            raw_children = [("condition", n.condition), ("body", n.body)]
        elif isinstance(n, Block):
            raw_children = [("stmt", s) for s in n.statements]
        elif isinstance(n, BinaryExpr):
            raw_children = [("left", n.left), ("right", n.right)]
        elif isinstance(n, UnaryExpr):
            raw_children = [("operand", n.operand)]

        for rel, child in raw_children:
            if child is not None:
                child_data = _serialize(child)
                child_data["relation"] = rel
                children_dict.append(child_data)

        return {
            "id": curr_id,
            "type": node_type,
            "label": label,
            "line": n.line,
            "column": n.column,
            "details": details,
            "children": children_dict,
        }

    return _serialize(node)



def render_ast_graph(node: ASTNode, output_path: str = "output/ast_tree") -> bool:
    """
    Safely renders the AST to an image file using Graphviz dot engine.
    Places generated artifacts cleanly inside a dedicated output directory.
    Gracefully handles missing python-graphviz package, missing 'dot' binary,
    file permission errors, or rendering failures without crashing the compiler.
    """
    from pathlib import Path

    # Ensure output path uses dedicated directory to keep root working directory clean
    target_path = Path(output_path)
    if target_path.parent == Path("."):
        target_path = Path("output") / target_path

    # Create parent output directory if it does not exist
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as err:
        print(f"Could not create AST output directory '{target_path.parent}': {err}. Skipping AST image generation.")
        return False

    dot_code = export_ast_dot(node)
    str_path = str(target_path)

    # 1. Try python graphviz library
    try:
        import graphviz
        try:
            src = graphviz.Source(dot_code)
            src.render(str_path, cleanup=True, format="png")
            print(f"📷 AST image rendered to '{str_path}.png'")
            return True
        except (graphviz.backend.ExecutableNotFound, FileNotFoundError):
            print("Graphviz not installed. Skipping AST image generation.")
            return False
        except Exception as err:
            if "dot" in str(err).lower() or "executable" in str(err).lower():
                print("Graphviz not installed. Skipping AST image generation.")
                return False
            print(f"Graphviz rendering failed: {err}. Skipping AST image generation.")
            return False
    except (ImportError, ModuleNotFoundError):
        pass  # Fall through to subprocess dot check

    # 2. Try subprocess dot executable directly
    try:
        import shutil
        import subprocess
        if not shutil.which("dot"):
            print("Graphviz not installed. Skipping AST image generation.")
            return False

        process = subprocess.run(
            ["dot", "-Tpng", "-o", f"{str_path}.png"],
            input=dot_code.encode("utf-8"),
            capture_output=True,
            check=True
        )
        print(f"📷 AST image rendered to '{str_path}.png'")
        return True
    except (FileNotFoundError, shutil.ExecError):
        print("Graphviz not installed. Skipping AST image generation.")
        return False
    except subprocess.CalledProcessError as err:
        print(f"Graphviz 'dot' execution failed with error code {err.returncode}. Skipping AST image generation.")
        return False
    except (OSError, PermissionError) as err:
        print(f"Could not write AST image file: {err}. Skipping AST image generation.")
        return False


