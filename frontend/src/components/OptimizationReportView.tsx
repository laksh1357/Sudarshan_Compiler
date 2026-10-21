import React, { useState } from 'react';
import { OptimizationRecord, OptimizationStats } from '../types/compiler';

interface OptimizationReportViewProps {
  report: OptimizationRecord[];
  stats?: OptimizationStats | null;
}

export const OptimizationReportView: React.FC<OptimizationReportViewProps> = ({
  report,
  stats,
}) => {
  const [copied, setCopied] = useState(false);

  // Generate observable behavior explanation text
  const behaviorText =
    report.length > 0
      ? report
          .map(
            (r, i) =>
              `Pass [${r.pass_name}]:\n  Original:    ${r.original}\n  Transformed: ${r.transformed}\n  Reason:      ${r.reason}`
          )
          .join('\n\n')
      : 'No transformation rules triggered for this program. Instructions were already in minimal canonical form or contained runtime-dependent variable references.';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(behaviorText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">7. Expected optimized behavior</div>
        <button onClick={handleCopy} className="btn-sm btn-ghost">
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <p className="section-desc">
        With optimization, the Sudarshan compiler applies multi-pass IR optimizations: constant expression folding, algebraic identity simplifications (e.g., <code>x + 0 → x</code>), and dead-code elimination.
      </p>

      {/* Structured Transformation Cards */}
      {report.length > 0 && (
        <div className="space-y-2 mb-4">
          {report.map((r, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg border border-studio-600 bg-black/25 text-xs font-mono space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  {r.pass_name}
                </span>
                <span className="text-studio-500 text-[11px] font-sans">{r.category}</span>
              </div>
              <div className="flex items-center gap-2 pt-1">
                <span className="text-red-400 line-through">{r.original}</span>
                <span className="text-studio-500">→</span>
                <span className="text-emerald-300 font-semibold">{r.transformed}</span>
              </div>
              <div className="text-studio-400 font-sans text-[11px] pt-0.5">
                {r.reason}
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="section-desc-bold">The important observable behavior is:</p>
      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">text</span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy text">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <pre className="code-view font-mono text-xs text-studio-300">{behaviorText}</pre>
      </div>
    </div>
  );
};
