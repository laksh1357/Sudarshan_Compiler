import React, { useState } from 'react';
import { TACInstructionItem } from '../types/compiler';

interface RawTACViewerProps {
  rawTac?: TACInstructionItem[] | null;
  rawTacText?: string | null;
}

export const RawTACViewer: React.FC<RawTACViewerProps> = ({ rawTac, rawTacText }) => {
  const [copied, setCopied] = useState(false);

  const tacInstructions = rawTac || [];
  const textContent =
    rawTacText ||
    tacInstructions.map((inst, i) => `${String(i).padStart(3, ' ')}:  ${inst.text}`).join('\n') ||
    'Run compilation to generate Intermediate Representation (TAC)...';

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
        <div className="pane-subheading">5. Raw Intermediate Representation (TAC)</div>
        <button onClick={handleCopy} className="btn-sm btn-ghost">
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      <p className="section-desc">
        Unoptimized Three-Address Code (-O0) generated from the Abstract Syntax Tree with temporary registers (t0, t1, ...):
      </p>

      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">
            unoptimized tac ({tacInstructions.length} instructions)
          </span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy TAC">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <div className="code-view font-mono text-xs text-sky-300">
          {tacInstructions.length > 0 ? (
            tacInstructions.map((inst, idx) => (
              <div key={idx} className="flex items-center gap-3 py-0.5 hover:bg-white/[0.04] px-1 rounded">
                <span className="text-studio-600 select-none text-[11px] w-8 text-right">
                  {idx}
                </span>
                <span className="text-sky-300">{inst.text}</span>
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
