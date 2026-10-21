import React, { useState } from 'react';
import { Zap, Copy, Check, SplitSquareVertical, ArrowRight, TrendingDown } from 'lucide-react';
import { TACInstructionItem, OptimizationStats } from '../types/compiler';

interface OptimizedTACViewerProps {
  rawInstructions?: TACInstructionItem[] | null;
  optInstructions?: TACInstructionItem[] | null;
  optText?: string | null;
  stats?: OptimizationStats | null;
}

export const OptimizedTACViewer: React.FC<OptimizedTACViewerProps> = ({
  rawInstructions,
  optInstructions,
  optText,
  stats,
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'optimized'>('side-by-side');
  const [copied, setCopied] = useState(false);

  if (!optInstructions || optInstructions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Zap className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">No Optimized IR Available</p>
        <p className="text-xs text-studio-500 mt-1">Compile your program with optimization enabled to inspect transformed TAC.</p>
      </div>
    );
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(optText || '');
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Ignore
    }
  };

  const rawCount = rawInstructions ? rawInstructions.length : 0;
  const optCount = optInstructions.length;
  const reduction = stats ? stats.reduction_percentage : 0;

  return (
    <div className="h-full flex flex-col bg-studio-900">
      {/* Header Bar */}
      <div className="p-3 border-b border-studio-700 flex flex-wrap items-center justify-between gap-2 bg-studio-850 select-none">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-studio-200">Optimized Three-Address Code</span>
          <div className="flex items-center gap-1.5 bg-studio-800 text-[11px] font-mono px-2 py-0.5 rounded border border-studio-700">
            <span className="text-studio-400">{rawCount}</span>
            <ArrowRight className="w-3 h-3 text-studio-500" />
            <span className="text-accent-green font-semibold">{optCount} insts</span>
            {reduction > 0 && (
              <span className="text-accent-green flex items-center gap-0.5 ml-1">
                <TrendingDown className="w-3 h-3" />
                <span>-{reduction}%</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-studio-800 p-0.5 rounded border border-studio-700 text-xs">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2 py-1 rounded font-medium transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-studio-700 text-white'
                  : 'text-studio-400 hover:text-studio-200'
              }`}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode('optimized')}
              className={`px-2 py-1 rounded font-medium transition-colors ${
                viewMode === 'optimized'
                  ? 'bg-studio-700 text-white'
                  : 'text-studio-400 hover:text-studio-200'
              }`}
            >
              Optimized Only
            </button>
          </div>

          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 text-xs text-studio-300 hover:text-white bg-studio-800 hover:bg-studio-750 rounded border border-studio-700 transition-colors"
          >
            {copied ? <Check className="w-3 h-3 text-accent-green" /> : <Copy className="w-3 h-3" />}
            <span>Copy</span>
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto p-4">
        {viewMode === 'side-by-side' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
            {/* Raw Column */}
            <div className="flex flex-col bg-studio-850 rounded-lg border border-studio-700 overflow-hidden">
              <div className="px-3 py-2 bg-studio-800 border-b border-studio-700 text-xs font-semibold text-studio-300 flex items-center justify-between">
                <span>Raw TAC (Before)</span>
                <span className="font-mono text-[11px] text-studio-400">{rawCount} insts</span>
              </div>
              <div className="p-3 overflow-auto flex-1 font-mono text-xs space-y-1">
                {rawInstructions?.map((inst) => (
                  <div key={inst.index} className="flex items-baseline gap-2 text-studio-400 py-0.5">
                    <span className="w-6 text-right text-studio-600 select-none">{inst.index}:</span>
                    <span className={inst.op === 'LABEL' ? 'text-accent-yellow font-semibold' : 'text-studio-300'}>
                      {inst.op === 'LABEL' ? `${inst.result}:` : inst.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Optimized Column */}
            <div className="flex flex-col bg-studio-850 rounded-lg border border-accent-green/30 overflow-hidden">
              <div className="px-3 py-2 bg-accent-green/10 border-b border-accent-green/20 text-xs font-semibold text-accent-green flex items-center justify-between">
                <span>Optimized TAC (After)</span>
                <span className="font-mono text-[11px] text-accent-green">{optCount} insts</span>
              </div>
              <div className="p-3 overflow-auto flex-1 font-mono text-xs space-y-1">
                {optInstructions.map((inst) => (
                  <div key={inst.index} className="flex items-baseline gap-2 py-0.5">
                    <span className="w-6 text-right text-studio-600 select-none">{inst.index}:</span>
                    <span className={inst.op === 'LABEL' ? 'text-accent-yellow font-semibold' : 'text-accent-green font-medium'}>
                      {inst.op === 'LABEL' ? `${inst.result}:` : inst.text}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Single Optimized List */
          <div className="max-w-2xl font-mono text-xs space-y-1">
            {optInstructions.map((inst) => (
              <div
                key={inst.index}
                className="flex items-baseline gap-4 py-0.5 px-2 rounded hover:bg-studio-800/60 transition-colors"
              >
                <span className="w-8 text-right text-studio-500 text-[11px] select-none font-mono">
                  {inst.index}:
                </span>
                <div className="flex-1">
                  {inst.op === 'LABEL' ? (
                    <span className="text-accent-yellow font-semibold">{inst.result}:</span>
                  ) : (
                    <span className="text-studio-200">{inst.text}</span>
                  )}
                </div>
                <span className="text-[10px] text-studio-500 uppercase px-1.5 py-0.2 rounded bg-studio-800 border border-studio-750 select-none">
                  {inst.op}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
