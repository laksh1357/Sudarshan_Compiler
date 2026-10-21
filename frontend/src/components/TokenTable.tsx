import React, { useState } from 'react';
import { Search, Filter, Hash } from 'lucide-react';
import { TokenItem } from '../types/compiler';

interface TokenTableProps {
  tokens?: TokenItem[] | null;
}

export const TokenTable: React.FC<TokenTableProps> = ({ tokens }) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  if (!tokens || tokens.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Hash className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">No Tokens Scanned</p>
        <p className="text-xs text-studio-500 mt-1">Compile your program to inspect the Lexer token stream.</p>
      </div>
    );
  }

  // Determine category for coloring
  const getCategory = (tok: TokenItem): string => {
    const t = tok.type;
    if (['INT', 'IF', 'ELSE', 'WHILE', 'PRINT'].includes(t)) return 'KEYWORD';
    if (t === 'ID') return 'IDENTIFIER';
    if (t === 'NUMBER') return 'NUMBER';
    if (['PLUS', 'MINUS', 'STAR', 'SLASH', 'ASSIGN', 'EQ', 'NEQ', 'LT', 'GT', 'LE', 'GE'].includes(t)) return 'OPERATOR';
    if (['LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'SEMICOLON'].includes(t)) return 'PUNCTUATION';
    if (t === 'EOF') return 'EOF';
    return 'OTHER';
  };

  const getBadgeStyle = (category: string) => {
    switch (category) {
      case 'KEYWORD':
        return 'bg-accent-red/10 text-accent-red border-accent-red/30';
      case 'IDENTIFIER':
        return 'bg-accent-blue/10 text-accent-blue border-accent-blue/30';
      case 'NUMBER':
        return 'bg-accent-green/10 text-accent-green border-accent-green/30';
      case 'OPERATOR':
        return 'bg-accent-purple/10 text-accent-purple border-accent-purple/30';
      case 'PUNCTUATION':
        return 'bg-studio-700 text-studio-300 border-studio-600';
      case 'EOF':
        return 'bg-studio-800 text-studio-500 border-studio-700';
      default:
        return 'bg-studio-700 text-studio-400 border-studio-600';
    }
  };

  const filteredTokens = tokens.filter((t) => {
    const category = getCategory(t);
    const matchesCategory = filterType === 'ALL' || category === filterType;
    const matchesSearch =
      t.type.toLowerCase().includes(search.toLowerCase()) ||
      String(t.value).toLowerCase().includes(search.toLowerCase()) ||
      String(t.line).includes(search);
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="h-full flex flex-col bg-studio-900">
      {/* Controls Bar */}
      <div className="p-3 border-b border-studio-700 flex flex-wrap items-center justify-between gap-2 bg-studio-850">
        <div className="flex items-center gap-2 flex-1 min-w-[200px]">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-studio-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search token value, type, line..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-studio-800 text-studio-200 text-xs pl-8 pr-3 py-1.5 rounded border border-studio-600 focus:outline-none focus:border-accent-blue font-sans"
            />
          </div>

          <div className="relative">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-studio-800 text-studio-200 text-xs px-2.5 py-1.5 rounded border border-studio-600 focus:outline-none focus:border-accent-blue font-sans cursor-pointer"
            >
              <option value="ALL">All Categories</option>
              <option value="KEYWORD">Keywords</option>
              <option value="IDENTIFIER">Identifiers</option>
              <option value="NUMBER">Literals</option>
              <option value="OPERATOR">Operators</option>
              <option value="PUNCTUATION">Punctuation</option>
              <option value="EOF">EOF</option>
            </select>
          </div>
        </div>

        <div className="text-xs font-mono text-studio-400 bg-studio-800 px-2 py-1 rounded border border-studio-700">
          <span>{filteredTokens.length} / {tokens.length} Tokens</span>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead className="sticky top-0 bg-studio-800 text-studio-400 font-mono uppercase text-[10px] tracking-wider border-b border-studio-700 z-10 select-none">
            <tr>
              <th className="py-2 px-3 w-12 text-center">#</th>
              <th className="py-2 px-3 w-36">Token Type</th>
              <th className="py-2 px-3">Lexeme / Value</th>
              <th className="py-2 px-3 w-28 text-right">Location</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-studio-800 font-mono text-studio-300">
            {filteredTokens.map((tok, idx) => {
              const cat = getCategory(tok);
              return (
                <tr key={idx} className="hover:bg-studio-800/50 transition-colors">
                  <td className="py-2 px-3 text-center text-studio-500">{idx + 1}</td>
                  <td className="py-2 px-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold border ${getBadgeStyle(cat)}`}>
                      {tok.type}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-studio-100 font-medium">
                    <code>{String(tok.value)}</code>
                  </td>
                  <td className="py-2 px-3 text-right text-studio-400">
                    L{tok.line}:C{tok.column}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
