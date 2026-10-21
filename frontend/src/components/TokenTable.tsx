import React, { useState } from 'react';
import { TokenItem } from '../types/compiler';

interface TokenTableProps {
  tokens?: TokenItem[] | null;
}

export const TokenTable: React.FC<TokenTableProps> = ({ tokens }) => {
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState('');

  if (!tokens || tokens.length === 0) {
    return (
      <div>
        <div className="pane-subheading-bar">
          <div className="pane-subheading">1. Expected lexical tokens</div>
        </div>
        <div className="code-view text-studio-500">
          Run compilation to inspect lexical tokens...
        </div>
      </div>
    );
  }

  // Generate formatted raw tokens text
  const tokensText = tokens
    .map(
      (t) =>
        `[Line ${t.line}:${t.column}] ${t.type.padEnd(16)} '${t.value !== null && t.value !== undefined ? t.value : ''}'`
    )
    .join('\n');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(tokensText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredTokens = filter
    ? tokens.filter(
        (t) =>
          t.type.toLowerCase().includes(filter.toLowerCase()) ||
          String(t.value).toLowerCase().includes(filter.toLowerCase())
      )
    : tokens;

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">1. Expected lexical tokens</div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Filter tokens..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-black/30 border border-studio-600 rounded px-2 py-0.5 text-xs font-mono text-studio-200 outline-none focus:border-indigo-500"
          />
          <button onClick={handleCopy} className="btn-sm btn-ghost">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">lexical tokens stream ({tokens.length} tokens)</span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy tokens">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <pre className="code-view font-mono text-xs text-studio-300">
          {filteredTokens.length > 0 ? (
            filteredTokens.map((t, idx) => (
              <div key={idx} className="hover:bg-white/[0.04] px-1 py-0.5 rounded flex items-center gap-3">
                <span className="text-studio-500 select-none text-[11px] w-20">
                  Line {t.line}:{t.column}
                </span>
                <span className="text-indigo-400 font-semibold w-36">{t.type}</span>
                <span className="text-emerald-300 font-mono">
                  {typeof t.value === 'string' ? `"${t.value}"` : String(t.value)}
                </span>
              </div>
            ))
          ) : (
            <div className="text-studio-500">No matching tokens found for "{filter}"</div>
          )}
        </pre>
      </div>
    </div>
  );
};
