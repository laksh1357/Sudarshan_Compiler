import React from 'react';
import { CompilerError } from '../types/compiler';

interface ErrorBannerProps {
  errors: CompilerError[];
  onDismiss: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ errors, onDismiss }) => {
  if (!errors || errors.length === 0) return null;

  return (
    <div className="error-banner">
      <div className="error-icon text-lg">⚠️</div>
      <div className="flex-1 flex flex-col gap-1">
        {errors.map((err, idx) => (
          <div key={idx} className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold uppercase tracking-wider text-xs px-1.5 py-0.5 rounded bg-red-900/40 border border-red-500/30">
              {err.phase} Phase
            </span>
            <span className="font-mono text-sm font-medium text-red-200">
              {err.error_type}: {err.message}
            </span>
            {err.line !== null && err.line !== undefined && (
              <span className="text-xs text-red-300/80 font-mono">
                [Line {err.line}{err.column !== null && err.column !== undefined ? `, Col ${err.column}` : ''}]
              </span>
            )}
            {err.source_context && (
              <div className="w-full text-xs font-mono text-studio-400 bg-black/40 px-2 py-1 rounded border border-red-500/20 mt-0.5 whitespace-pre-wrap">
                {err.source_context}
              </div>
            )}
          </div>
        ))}
      </div>
      <button
        onClick={onDismiss}
        className="error-close hover:text-white transition-colors"
        title="Dismiss error notice"
      >
        ×
      </button>
    </div>
  );
};
