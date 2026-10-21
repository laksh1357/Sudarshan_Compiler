import React from 'react';
import { Table2, Box, Info } from 'lucide-react';
import { SymbolTableData } from '../types/compiler';

interface SymbolTableViewProps {
  symbolTable?: SymbolTableData | null;
}

export const SymbolTableView: React.FC<SymbolTableViewProps> = ({ symbolTable }) => {
  if (!symbolTable || !symbolTable.symbols || symbolTable.symbols.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Table2 className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">No Symbols Declared</p>
        <p className="text-xs text-studio-500 mt-1">Declare variables with `int x = ...;` to populate the Symbol Table.</p>
      </div>
    );
  }

  const { symbols, scopes } = symbolTable;

  return (
    <div className="h-full flex flex-col bg-studio-900 overflow-auto p-4 gap-4">
      {/* Scope Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <Box className="w-4 h-4 text-accent-blue" />
            <span>Total Symbols</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">{symbols.length}</div>
        </div>

        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <Box className="w-4 h-4 text-accent-purple" />
            <span>Scope Environments</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">{scopes.length}</div>
        </div>

        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <Box className="w-4 h-4 text-accent-green" />
            <span>Maximum Nesting Depth</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {Math.max(...scopes.map((s) => s.scope_level), 0)}
          </div>
        </div>
      </div>

      {/* Symbol Table */}
      <div className="bg-studio-850 rounded-lg border border-studio-700 overflow-hidden">
        <div className="px-3 py-2.5 bg-studio-800 border-b border-studio-700 font-semibold text-xs text-studio-200 flex items-center justify-between">
          <span>Identified Variable Symbols</span>
          <span className="text-[11px] font-mono text-studio-400">Scoped Symbol Resolution</span>
        </div>

        <table className="w-full text-left text-xs border-collapse">
          <thead className="bg-studio-800/60 text-studio-400 font-mono uppercase text-[10px] tracking-wider border-b border-studio-700">
            <tr>
              <th className="py-2.5 px-3">Identifier Name</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Scope Level</th>
              <th className="py-2.5 px-3 text-right">Declared At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-studio-800 font-mono text-studio-300">
            {symbols.map((sym, idx) => (
              <tr key={idx} className="hover:bg-studio-800/40 transition-colors">
                <td className="py-2.5 px-3 font-semibold text-accent-blue">
                  {sym.name}
                </td>
                <td className="py-2.5 px-3">
                  <span className="px-2 py-0.5 rounded text-[11px] bg-studio-700 text-studio-300 border border-studio-600">
                    {sym.type_name}
                  </span>
                </td>
                <td className="py-2.5 px-3">
                  <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${
                    sym.scope_level === 0
                      ? 'bg-accent-blue/10 text-accent-blue border-accent-blue/30'
                      : 'bg-accent-purple/10 text-accent-purple border-accent-purple/30'
                  }`}>
                    {sym.scope_level === 0 ? 'Scope 0 (Global)' : `Scope ${sym.scope_level} (Block)`}
                  </span>
                </td>
                <td className="py-2.5 px-3 text-right text-studio-400">
                  {sym.line !== null && sym.line !== undefined ? `Line ${sym.line}:${sym.column}` : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Scoping Explanation Card */}
      <div className="p-3 bg-studio-850/60 rounded-lg border border-studio-750 text-xs text-studio-400 leading-relaxed flex items-start gap-2.5">
        <Info className="w-4 h-4 text-accent-blue shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-studio-300">Lexical Block Scoping & Shadowing:</span> Variables declared inside nested blocks (<code className="text-accent-blue font-mono">{'{ ... }'}</code>) are assigned incremented scope levels. If an inner variable shares the same name as an outer variable, it shadows the outer symbol for the duration of that block without overwriting it.
        </div>
      </div>
    </div>
  );
};
