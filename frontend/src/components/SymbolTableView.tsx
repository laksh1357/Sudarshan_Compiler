import React, { useState } from 'react';
import { SymbolTableData } from '../types/compiler';

interface SymbolTableViewProps {
  symbolTable?: SymbolTableData | null;
}

export const SymbolTableView: React.FC<SymbolTableViewProps> = ({ symbolTable }) => {
  const [copied, setCopied] = useState(false);

  // Flatten symbols with scope information
  const symbols = symbolTable?.symbols || [];

  // Generate formatted raw symbol table text
  const rawText = symbols.length > 0
    ? [
        '-----------------------------------------------------------------',
        'NAME             TYPE       KIND       SCOPE            LINE:COL',
        '-----------------------------------------------------------------',
        ...symbols.map((s) => {
          const scopeLabel = s.scope_level === 0 ? 'global' : `scope_level_${s.scope_level}`;
          const pos = s.line ? `${s.line}:${s.column || 1}` : '-';
          return `${s.name.padEnd(16)} ${(s.type_name || 'int').padEnd(10)} ${'variable'.padEnd(10)} ${scopeLabel.padEnd(16)} ${pos}`;
        }),
        '-----------------------------------------------------------------',
      ].join('\n')
    : 'No symbols recorded yet.';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(rawText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  const hasNestedScopes = symbols.some((s) => s.scope_level > 0);

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">3. Expected Symbol table</div>
        <button onClick={handleCopy} className="btn-sm btn-ghost">
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <p className="section-desc">
        A scope-aware table showing tracked identifiers, inferred types, lexical scope levels, and declaration bindings:
      </p>

      {/* 5-Column Table */}
      <div className="table-wrapper">
        <table className="sym-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Kind</th>
              <th>Scope</th>
              <th>Value/Binding</th>
            </tr>
          </thead>
          <tbody>
            {symbols.length > 0 ? (
              symbols.map((sym, idx) => {
                const scopeName = sym.scope_level === 0 ? 'global' : `block_level_${sym.scope_level}`;
                return (
                  <tr key={idx}>
                    <td>
                      <strong className="text-white font-mono">{sym.name}</strong>
                    </td>
                    <td>
                      <span className="badge-type">{sym.type_name || 'int'}</span>
                    </td>
                    <td>
                      <span className="badge-kind">variable</span>
                    </td>
                    <td>
                      <span className="badge-scope">{scopeName}</span>
                    </td>
                    <td>
                      <span className="badge-value">
                        {sym.line ? `Decl @ Line ${sym.line}` : 'initialized'}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} className="empty-state">
                  No symbols recorded yet. Run compilation to populate the symbol table.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Code Box Wrapper */}
      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">text</span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy text">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <pre className="code-view font-mono text-xs text-studio-300">{rawText}</pre>
      </div>

      {/* Scope Note */}
      <p className="scope-note">
        {hasNestedScopes ? (
          <>
            Variables declared within <code>while</code> loops or <code>if/else</code> blocks are bound to their local lexical block scope and cannot be accessed outside their declaring block.
          </>
        ) : (
          <>
            All identifiers currently reside in the <code>global</code> scope. Introducing curly brace blocks (<code>&#123; ... &#125;</code>) creates isolated child scopes.
          </>
        )}
      </p>
    </div>
  );
};
