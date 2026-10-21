import React, { useState } from 'react';
import {
  Network,
  ChevronRight,
  ChevronDown,
  Layers,
  FileText,
  Copy,
  Check,
  Code2
} from 'lucide-react';
import { ASTNodeData } from '../types/compiler';

interface ASTViewerProps {
  ast?: ASTNodeData | null;
  astText?: string | null;
  astDot?: string | null;
}

// Recursive AST Node Component
const ASTTreeNode: React.FC<{
  node: ASTNodeData;
  depth?: number;
  isLast?: boolean;
}> = ({ node, depth = 0, isLast = true }) => {
  const [collapsed, setCollapsed] = useState(false);
  const hasChildren = node.children && node.children.length > 0;

  // Node type styling
  const getNodeColor = (type: string) => {
    switch (type) {
      case 'Program':
        return 'text-accent-blue bg-accent-blue/10 border-accent-blue/30';
      case 'VarDecl':
        return 'text-accent-green bg-accent-green/10 border-accent-green/30';
      case 'Assignment':
        return 'text-accent-orange bg-accent-orange/10 border-accent-orange/30';
      case 'PrintStmt':
        return 'text-accent-purple bg-accent-purple/10 border-accent-purple/30';
      case 'IfStmt':
      case 'WhileStmt':
        return 'text-accent-yellow bg-accent-yellow/10 border-accent-yellow/30';
      case 'Block':
        return 'text-studio-300 bg-studio-700 border-studio-600';
      case 'BinaryExpr':
      case 'UnaryExpr':
        return 'text-accent-blue bg-studio-800 border-studio-600';
      case 'IntegerLiteral':
        return 'text-accent-green bg-studio-850 border-studio-700';
      case 'Variable':
        return 'text-studio-200 bg-studio-850 border-studio-700';
      default:
        return 'text-studio-400 bg-studio-800 border-studio-700';
    }
  };

  return (
    <div className="font-mono text-xs select-none">
      <div className="flex items-center gap-1.5 py-1 px-1.5 rounded hover:bg-studio-800/60 transition-colors group">
        {/* Expand / Collapse toggle */}
        {hasChildren ? (
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-4 h-4 rounded hover:bg-studio-700 flex items-center justify-center text-studio-400"
          >
            {collapsed ? <ChevronRight className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        ) : (
          <span className="w-4 h-4 flex items-center justify-center text-studio-600 text-[10px]">•</span>
        )}

        {/* Relation badge if any (e.g. left, right, cond, then, else) */}
        {node.relation && (
          <span className="text-[10px] uppercase font-semibold text-studio-500 bg-studio-800/80 px-1 py-0.2 rounded border border-studio-700">
            {node.relation}
          </span>
        )}

        {/* Node Badge */}
        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getNodeColor(node.type)}`}>
          {node.label}
        </span>

        {/* Node Location */}
        {node.line !== null && node.line !== undefined && (
          <span className="text-[10px] text-studio-500 opacity-0 group-hover:opacity-100 transition-opacity">
            L{node.line}:C{node.column}
          </span>
        )}
      </div>

      {/* Render Children */}
      {hasChildren && !collapsed && (
        <div className="ml-5 pl-2 border-l border-studio-750 flex flex-col gap-0.5 mt-0.5">
          {node.children.map((child, idx) => (
            <ASTTreeNode
              key={child.id || idx}
              node={child}
              depth={depth + 1}
              isLast={idx === node.children.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const ASTViewer: React.FC<ASTViewerProps> = ({
  ast,
  astText,
  astDot,
}) => {
  const [viewMode, setViewMode] = useState<'visual' | 'text' | 'dot'>('visual');
  const [copied, setCopied] = useState(false);

  if (!ast) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Network className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">No AST Available</p>
        <p className="text-xs text-studio-500 mt-1">Compile source code to generate and inspect the Abstract Syntax Tree.</p>
      </div>
    );
  }

  const handleCopy = async () => {
    const textToCopy = viewMode === 'dot' ? (astDot || '') : (astText || '');
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore
    }
  };

  return (
    <div className="h-full flex flex-col bg-studio-900">
      {/* Controls Bar */}
      <div className="p-3 border-b border-studio-700 flex items-center justify-between gap-2 bg-studio-850">
        <div className="flex items-center gap-1.5 bg-studio-800 p-0.5 rounded border border-studio-700">
          <button
            onClick={() => setViewMode('visual')}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded font-medium transition-colors ${
              viewMode === 'visual'
                ? 'bg-studio-700 text-white'
                : 'text-studio-400 hover:text-studio-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Interactive Tree</span>
          </button>

          <button
            onClick={() => setViewMode('text')}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded font-medium transition-colors ${
              viewMode === 'text'
                ? 'bg-studio-700 text-white'
                : 'text-studio-400 hover:text-studio-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Indented Hierarchy</span>
          </button>

          <button
            onClick={() => setViewMode('dot')}
            className={`flex items-center gap-1 px-2.5 py-1 text-xs rounded font-medium transition-colors ${
              viewMode === 'dot'
                ? 'bg-studio-700 text-white'
                : 'text-studio-400 hover:text-studio-200'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Graphviz DOT</span>
          </button>
        </div>

        {viewMode !== 'visual' && (
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-studio-400 hover:text-studio-200 bg-studio-800 hover:bg-studio-750 rounded border border-studio-700 transition-colors"
          >
            {copied ? <Check className="w-3 h-3 text-accent-green" /> : <Copy className="w-3 h-3" />}
            <span>Copy</span>
          </button>
        )}
      </div>

      {/* View Content */}
      <div className="flex-1 overflow-auto p-4">
        {viewMode === 'visual' && (
          <div className="max-w-3xl">
            <ASTTreeNode node={ast} />
          </div>
        )}

        {viewMode === 'text' && (
          <pre className="font-mono text-xs text-studio-300 leading-relaxed whitespace-pre-wrap select-text">
            {astText || 'No text tree available'}
          </pre>
        )}

        {viewMode === 'dot' && (
          <pre className="font-mono text-xs text-accent-blue/90 leading-relaxed whitespace-pre-wrap select-text">
            {astDot || 'No DOT graph syntax available'}
          </pre>
        )}
      </div>
    </div>
  );
};
