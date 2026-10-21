import React from 'react';
import { AlertCircle, FileCode } from 'lucide-react';
import { CompilerError } from '../types/compiler';

interface ErrorBannerProps {
  error: CompilerError;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ error }) => {
  return (
    <div className="m-3 p-3.5 bg-accent-red/10 border border-accent-red/30 rounded-lg text-studio-200">
      <div className="flex items-start gap-2.5">
        <AlertCircle className="w-5 h-5 text-accent-red shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-accent-red text-xs tracking-wider uppercase">
              {error.error_type}
            </span>
            {error.line !== null && error.line !== undefined && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-accent-red/20 text-accent-red font-mono">
                Line {error.line}{error.column !== null && error.column !== undefined ? `:${error.column}` : ''}
              </span>
            )}
          </div>
          <p className="text-xs text-studio-300 mt-1 font-sans leading-relaxed">
            {error.message}
          </p>

          {error.source_context && (
            <div className="mt-2.5 p-2 bg-studio-950/80 rounded border border-accent-red/20 font-mono text-xs text-accent-red">
              <pre className="whitespace-pre-wrap">{error.source_context}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
