import React, { useState } from 'react';
import { Play, PlayCircle, Copy, Check, Trash2, RotateCcw, BookOpen, Clock } from 'lucide-react';
import { ExampleProgram, TimingData } from '../types/compiler';

interface EditorToolbarProps {
  examples: ExampleProgram[];
  selectedExampleId: string;
  onSelectExample: (example: ExampleProgram) => void;
  onCompile: () => void;
  onCompileAndRun: () => void;
  onClear: () => void;
  onReset: () => void;
  sourceCode: string;
  isCompiling: boolean;
  timing?: TimingData;
}

export const EditorToolbar: React.FC<EditorToolbarProps> = ({
  examples,
  selectedExampleId,
  onSelectExample,
  onCompile,
  onCompileAndRun,
  onClear,
  onReset,
  sourceCode,
  isCompiling,
  timing,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(sourceCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore
    }
  };

  // Group examples by category
  const categories: Record<string, ExampleProgram[]> = {};
  examples.forEach((ex) => {
    const cat = ex.category || 'General';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push(ex);
  });

  return (
    <div className="h-11 border-b border-studio-600 bg-studio-850 px-3 flex items-center justify-between gap-2 select-none overflow-x-auto">
      {/* Left: Example Selector & Execution Actions */}
      <div className="flex items-center gap-2">
        {/* Example Selector */}
        <div className="relative flex items-center">
          <BookOpen className="w-3.5 h-3.5 text-studio-400 absolute left-2.5 pointer-events-none" />
          <select
            value={selectedExampleId}
            onChange={(e) => {
              const found = examples.find((ex) => ex.id === e.target.value);
              if (found) onSelectExample(found);
            }}
            className="bg-studio-800 text-studio-200 text-xs pl-8 pr-7 py-1.5 rounded border border-studio-600 focus:outline-none focus:border-accent-blue font-sans cursor-pointer hover:bg-studio-750 transition-colors"
          >
            {Object.entries(categories).map(([cat, exList]) => (
              <optgroup key={cat} label={`── ${cat} ──`} className="bg-studio-900 text-studio-300">
                {exList.map((ex) => (
                  <option key={ex.id} value={ex.id} className="bg-studio-850 text-studio-200">
                    {ex.name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </div>

        {/* Separator */}
        <div className="w-[1px] h-5 bg-studio-600 mx-1" />

        {/* Compile Button */}
        <button
          onClick={onCompile}
          disabled={isCompiling}
          title="Compile source code through AST, Semantic, and TAC phases"
          className="flex items-center gap-1.5 px-3 py-1.5 bg-studio-700 hover:bg-studio-600 text-studio-100 disabled:opacity-50 text-xs font-medium rounded border border-studio-600 transition-colors shadow-sm"
        >
          <Play className="w-3.5 h-3.5 text-accent-blue" />
          <span>Compile</span>
        </button>

        {/* Compile & Run Button */}
        <button
          onClick={onCompileAndRun}
          disabled={isCompiling}
          title="Compile and execute program on Sudarshan Virtual Machine"
          className="flex items-center gap-1.5 px-3.5 py-1.5 bg-accent-blue/20 hover:bg-accent-blue/30 text-accent-blue border border-accent-blue/40 hover:border-accent-blue/60 disabled:opacity-50 text-xs font-semibold rounded transition-all shadow-sm"
        >
          <PlayCircle className="w-3.5 h-3.5" />
          <span>Compile & Run</span>
        </button>
      </div>

      {/* Right: Code Helpers & Timing */}
      <div className="flex items-center gap-2">
        {timing && timing.total_ms > 0 && (
          <div className="hidden lg:flex items-center gap-1.5 text-[11px] font-mono text-studio-400 bg-studio-800 px-2 py-1 rounded border border-studio-700">
            <Clock className="w-3 h-3 text-accent-green" />
            <span>{timing.total_ms.toFixed(1)} ms</span>
          </div>
        )}

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          title="Copy source code to clipboard"
          className="p-1.5 text-studio-400 hover:text-studio-200 hover:bg-studio-800 rounded border border-studio-600 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-accent-green" /> : <Copy className="w-3.5 h-3.5" />}
        </button>

        {/* Reset to Example Code */}
        <button
          onClick={onReset}
          title="Revert modifications back to example code"
          className="p-1.5 text-studio-400 hover:text-studio-200 hover:bg-studio-800 rounded border border-studio-600 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Clear Code */}
        <button
          onClick={onClear}
          title="Clear editor buffer"
          className="p-1.5 text-studio-400 hover:text-accent-red hover:bg-studio-800 rounded border border-studio-600 transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
