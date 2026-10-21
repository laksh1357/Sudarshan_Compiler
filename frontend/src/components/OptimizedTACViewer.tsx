import React, { useState } from 'react';
import { TACInstructionItem, OptimizationStats } from '../types/compiler';

interface OptimizedTACViewerProps {
  optimizedTac?: TACInstructionItem[] | null;
  optimizedTacText?: string | null;
  stats?: OptimizationStats | null;
}

export const OptimizedTACViewer: React.FC<OptimizedTACViewerProps> = ({
  optimizedTac,
  optimizedTacText,
  stats,
}) => {
  const [copied, setCopied] = useState(false);

  const tacInstructions = optimizedTac || [];
  const textContent =
    optimizedTacText ||
    tacInstructions.map((inst, i) => `${String(i).padStart(3, ' ')}:  ${inst.text}`).join('\n') ||
    'Run compilation with optimizations enabled to inspect optimized TAC...';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">6. Expected optimized IR</div>
        <div className="flex items-center gap-2">
          {stats && (
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
              {stats.original_count} → {stats.optimized_count} insts ({stats.reduction_percentage}% reduction)
            </span>
          )}
          <button onClick={handleCopy} className="btn-sm btn-ghost">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <p className="section-desc">
        Optimized Three-Address Code with constant folding, algebraic simplification, and dead-code elimination applied:
      </p>

      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">
            optimized tac ({tacInstructions.length} instructions)
          </span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy TAC">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <div className="code-view font-mono text-xs text-indigo-300">
          {tacInstructions.length > 0 ? (
            tacInstructions.map((inst, idx) => (
              <div key={idx} className="flex items-center gap-3 py-0.5 hover:bg-white/[0.04] px-1 rounded">
                <span className="text-studio-600 select-none text-[11px] w-8 text-right">
                  {idx}
                </span>
                <span className="text-indigo-200">{inst.text}</span>
              </div>
            ))
          ) : (
            <div className="text-studio-500">{textContent}</div>
          )}
        </div>
      </div>
    </div>
  );
};
