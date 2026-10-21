import React, { useState, useMemo, useRef, useEffect } from 'react';
import { ASTNodeData } from '../types/compiler';

interface ASTViewerProps {
  ast?: ASTNodeData | null;
  astText?: string | null;
}

interface LayoutNode {
  id: string;
  label: string;
  sublabel: string;
  category: 'root' | 'stmt' | 'expr' | 'leaf';
  children: LayoutNode[];
  subtreeWidth?: number;
  x?: number;
  y?: number;
}

export const ASTViewer: React.FC<ASTViewerProps> = ({ ast, astText }) => {
  const [viewMode, setViewMode] = useState<'graph' | 'cards' | 'text'>('graph');
  const [copied, setCopied] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Transform raw AST into simplified LayoutNode tree
  const treeRoot = useMemo(() => {
    if (!ast) return null;

    function buildNode(data: any): LayoutNode | null {
      if (!data) return null;

      let label = data.label || data.type || 'Node';
      let sublabel = data.line ? `Line ${data.line}` : '';
      let category: 'root' | 'stmt' | 'expr' | 'leaf' = 'expr';
      let rawChildren: any[] = [];

      const t = data.type || '';

      if (t === 'Program' || t === 'Block') {
        label = t === 'Program' ? 'Root Program' : 'Code Block';
        const stmtsCount = data.children ? data.children.length : (data.details?.statements_count || 0);
        sublabel = `${stmtsCount} Stmts`;
        category = 'root';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Declaration') || t === 'VarDecl' || t === 'DeclarationStmt') {
        const varName = data.details?.name || data.label?.replace('Decl: ', '') || '';
        const varType = data.details?.type || 'int';
        label = `Decl: ${varType} ${varName}`;
        category = 'stmt';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Assignment') || t === 'Assign' || t === 'AssignmentStmt') {
        const varName = data.details?.name || data.label?.replace('Assign: ', '') || '';
        label = `Assign: ${varName}`;
        category = 'stmt';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Print') || t === 'PrintStmt') {
        label = 'print()';
        category = 'stmt';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('While') || t === 'WhileStmt') {
        label = 'WhileLoop';
        category = 'stmt';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('If') || t === 'IfStmt') {
        label = 'IfBranch';
        category = 'stmt';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Binary') || t === 'BinaryOp') {
        const op = data.details?.operator || data.label?.replace('Op: ', '') || 'Op';
        label = `Op: ${op}`;
        category = 'expr';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Unary') || t === 'UnaryOp') {
        const op = data.details?.operator || '-';
        label = `Unary: ${op}`;
        category = 'expr';
        if (data.children) rawChildren = data.children;
      } else if (t.includes('Literal') || t === 'Integer' || t === 'NumberLiteral' || t === 'IntegerExpr') {
        const val = data.details?.value !== undefined ? data.details.value : data.label;
        label = `Val: ${val}`;
        category = 'leaf';
      } else if (t.includes('Identifier') || t === 'Variable' || t === 'VariableExpr') {
        const name = data.details?.name || data.label;
        label = `Var: ${name}`;
        category = 'leaf';
      } else {
        if (data.children) rawChildren = data.children;
      }

      const childNodes = rawChildren
        .map((c) => buildNode(c))
        .filter((c): c is LayoutNode => c !== null);

      return {
        id: data.id || Math.random().toString(),
        label,
        sublabel,
        category,
        children: childNodes,
      };
    }

    return buildNode(ast);
  }, [ast]);

  // Compute Layout Positions (x, y)
  const layout = useMemo(() => {
    if (!treeRoot) return null;

    const NODE_WIDTH = 135;
    const NODE_HEIGHT = 44;
    const LEVEL_GAP = 70;
    const SIBLING_GAP = 24;

    function calcSubtreeWidth(node: LayoutNode): number {
      if (!node.children || node.children.length === 0) {
        node.subtreeWidth = NODE_WIDTH + SIBLING_GAP;
        return node.subtreeWidth;
      }
      let w = 0;
      node.children.forEach((c) => {
        w += calcSubtreeWidth(c);
      });
      node.subtreeWidth = Math.max(w, NODE_WIDTH + SIBLING_GAP);
      return node.subtreeWidth;
    }

    calcSubtreeWidth(treeRoot);

    let maxDepth = 0;
    function assignCoords(node: LayoutNode, leftX: number, depth: number) {
      maxDepth = Math.max(maxDepth, depth);
      node.y = 45 + depth * (NODE_HEIGHT + LEVEL_GAP);

      if (!node.children || node.children.length === 0) {
        node.x = leftX + (node.subtreeWidth || NODE_WIDTH) / 2;
      } else {
        let curLeft = leftX;
        node.children.forEach((c) => {
          assignCoords(c, curLeft, depth + 1);
          curLeft += c.subtreeWidth || NODE_WIDTH;
        });
        const firstChild = node.children[0];
        const lastChild = node.children[node.children.length - 1];
        node.x = ((firstChild.x || 0) + (lastChild.x || 0)) / 2;
      }
    }

    assignCoords(treeRoot, 30, 0);

    const totalWidth = Math.max((treeRoot.subtreeWidth || 800) + 80, 850);
    const totalHeight = 70 + (maxDepth + 1) * (NODE_HEIGHT + LEVEL_GAP);

    // Flatten nodes and edges for SVG rendering
    const allNodes: LayoutNode[] = [];
    const allEdges: Array<{ id: string; x1: number; y1: number; x2: number; y2: number }> = [];

    function collect(node: LayoutNode) {
      allNodes.push(node);
      node.children.forEach((child) => {
        allEdges.push({
          id: `${node.id}-${child.id}`,
          x1: node.x!,
          y1: node.y! + NODE_HEIGHT / 2,
          x2: child.x!,
          y2: child.y! - NODE_HEIGHT / 2,
        });
        collect(child);
      });
    }

    collect(treeRoot);

    return {
      totalWidth,
      totalHeight,
      nodes: allNodes,
      edges: allEdges,
      NODE_WIDTH,
      NODE_HEIGHT,
    };
  }, [treeRoot]);

  // Center the graph on initial render
  useEffect(() => {
    if (viewMode === 'graph' && containerRef.current && layout) {
      const container = containerRef.current;
      const scrollX = Math.max(0, (layout.totalWidth - container.clientWidth) / 2);
      container.scrollLeft = scrollX;
    }
  }, [viewMode, layout]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(astText || JSON.stringify(ast, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  if (!ast && !astText) {
    return (
      <div>
        <div className="pane-subheading-bar">
          <div className="pane-subheading">2. Expected AST</div>
        </div>
        <div className="code-view text-studio-500">
          Run compilation to inspect the Abstract Syntax Tree...
        </div>
      </div>
    );
  }

  // Recursive Card Renderer for 'cards' view
  const renderCard = (node: LayoutNode, depth: number = 0) => {
    return (
      <div key={node.id} style={{ marginLeft: `${depth * 20}px` }} className="mb-1.5">
        <div className="ast-node-card">
          <div className="ast-node-title flex items-center gap-2">
            <span>
              {node.category === 'root'
                ? '📁'
                : node.category === 'stmt'
                ? '🔹'
                : node.category === 'expr'
                ? '⚡'
                : '🔢'}
            </span>
            <span>{node.label}</span>
          </div>
          {node.sublabel && (
            <span className="ast-node-detail font-mono">{node.sublabel}</span>
          )}
        </div>
        {node.children && node.children.map((c) => renderCard(c, depth + 1))}
      </div>
    );
  };

  return (
    <div>
      {/* Subheading & View Switcher */}
      <div className="pane-subheading-bar">
        <div className="pane-subheading">2. Expected AST</div>
        <div className="view-toggle">
          <button
            onClick={() => setViewMode('graph')}
            className={`toggle-btn ${viewMode === 'graph' ? 'active' : ''}`}
          >
            🌳 Graph Tree
          </button>
          <button
            onClick={() => setViewMode('cards')}
            className={`toggle-btn ${viewMode === 'cards' ? 'active' : ''}`}
          >
            📋 List View
          </button>
          <button
            onClick={() => setViewMode('text')}
            className={`toggle-btn ${viewMode === 'text' ? 'active' : ''}`}
          >
            📄 Text View
          </button>
        </div>
      </div>

      {/* Mode 1: Interactive SVG Graph Tree */}
      {viewMode === 'graph' && (
        <div ref={containerRef} className="ast-graph-container">
          {layout ? (
            <svg
              className="ast-svg"
              width={layout.totalWidth}
              height={layout.totalHeight}
              style={{ minWidth: `${layout.totalWidth}px`, minHeight: `${layout.totalHeight}px` }}
            >
              {/* Edges */}
              {layout.edges.map((edge) => {
                const midY = (edge.y1 + edge.y2) / 2;
                const pathData = `M ${edge.x1} ${edge.y1} C ${edge.x1} ${midY}, ${edge.x2} ${midY}, ${edge.x2} ${edge.y2}`;
                return <path key={edge.id} d={pathData} className="tree-edge" />;
              })}

              {/* Nodes */}
              {layout.nodes.map((node) => {
                const left = (node.x || 0) - layout.NODE_WIDTH / 2;
                const top = (node.y || 0) - layout.NODE_HEIGHT / 2;
                return (
                  <g
                    key={node.id}
                    className="tree-node-group"
                    transform={`translate(${left}, ${top})`}
                  >
                    <rect
                      width={layout.NODE_WIDTH}
                      height={layout.NODE_HEIGHT}
                      className={`tree-node-rect ${node.category}`}
                    />
                    <text
                      x={layout.NODE_WIDTH / 2}
                      y={node.sublabel ? layout.NODE_HEIGHT / 2 - 3 : layout.NODE_HEIGHT / 2 + 4}
                      className="tree-node-text"
                    >
                      {node.label}
                    </text>
                    {node.sublabel && (
                      <text
                        x={layout.NODE_WIDTH / 2}
                        y={layout.NODE_HEIGHT / 2 + 11}
                        className="tree-node-subtext"
                      >
                        {node.sublabel}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>
          ) : (
            <div className="p-8 text-center text-studio-500">Could not calculate AST layout.</div>
          )}
        </div>
      )}

      {/* Mode 2: Card List View */}
      {viewMode === 'cards' && (
        <div className="ast-visualizer overflow-auto max-h-[calc(100vh-210px)] pr-2">
          {treeRoot ? (
            <div className="ast-tree">{renderCard(treeRoot, 0)}</div>
          ) : (
            <div className="text-studio-500">No AST cards available.</div>
          )}
        </div>
      )}

      {/* Mode 3: Text View */}
      {viewMode === 'text' && (
        <div className="code-box-wrapper">
          <div className="code-box-header">
            <span className="code-box-title">text</span>
            <button className="copy-icon-btn" onClick={handleCopy} title="Copy text">
              {copied ? '✓' : '📋'}
            </button>
          </div>
          <pre className="code-view font-mono text-xs text-studio-300">
            {astText || JSON.stringify(ast, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
