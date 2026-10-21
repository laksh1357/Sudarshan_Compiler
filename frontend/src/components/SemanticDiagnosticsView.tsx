import React from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, AlertCircle, FileCode } from 'lucide-react';
import { SemanticDiagnostic, CompilerError } from '../types/compiler';

interface SemanticDiagnosticsViewProps {
  diagnostics: SemanticDiagnostic[];
  errors: CompilerError[];
  success: boolean;
}

export const SemanticDiagnosticsView: React.FC<SemanticDiagnosticsViewProps> = ({
  diagnostics,
  errors,
  success,
}) => {
  const semanticErrors = errors.filter((e) => e.phase === 'semantic');
  const hasSemanticError = semanticErrors.length > 0;

  return (
    <div className="h-full flex flex-col bg-studio-900 overflow-auto p-4 gap-4">
      {/* Top Status Banner */}
      {hasSemanticError ? (
        <div className="p-4 bg-accent-red/10 border border-accent-red/30 rounded-lg flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-accent-red shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-accent-red">Semantic Analysis Failed</h3>
            <p className="text-xs text-studio-300 mt-1">
              Static semantic analyzer detected scope violations or undeclared variable references.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-4 bg-accent-green/10 border border-accent-green/30 rounded-lg flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-accent-green shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-accent-green">Semantic Validation Passed</h3>
            <p className="text-xs text-studio-300 mt-1">
              All variable declarations, lexical scopes, types, and identifier references verified successfully.
            </p>
          </div>
        </div>
      )}

      {/* Semantic Checks Performed */}
      <div className="bg-studio-850 rounded-lg border border-studio-700 p-4">
        <h4 className="text-xs font-semibold text-studio-200 uppercase tracking-wider mb-3">
          Compiler Semantic Verification Rules
        </h4>

        <div className="space-y-2.5 text-xs text-studio-300">
          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-white">Declaration Before Use:</span> Every identifier referenced in expressions or assignments must have an active declaration in the current or ancestor lexical scope.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-white">Duplicate Declaration Protection:</span> Redundant variable redeclaration in the same scope environment is prohibited and flagged as an error.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-white">Block Scope Isolation & Shadowing:</span> Nested scopes permit variable shadowing while strictly encapsulating block variables upon scope exit.
            </div>
          </div>

          <div className="flex items-start gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-accent-green shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-white">Type Invariance:</span> Arithmetic expressions, conditions, and assignment targets are validated for integer type compatibility.
            </div>
          </div>
        </div>
      </div>

      {/* Error Details if any */}
      {semanticErrors.map((err, idx) => (
        <div key={idx} className="p-3.5 bg-accent-red/10 border border-accent-red/30 rounded-lg text-studio-200">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-accent-red shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-accent-red text-xs">{err.error_type}</span>
                {err.line && (
                  <span className="text-[11px] px-1.5 py-0.2 rounded bg-accent-red/20 text-accent-red font-mono">
                    Line {err.line}:{err.column}
                  </span>
                )}
              </div>
              <p className="text-xs text-studio-300 mt-1 font-sans">{err.message}</p>
              {err.source_context && (
                <div className="mt-2 p-2 bg-studio-950 rounded border border-accent-red/20 font-mono text-xs text-accent-red">
                  <pre className="whitespace-pre-wrap">{err.source_context}</pre>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}

      {/* Diagnostics List */}
      {diagnostics.length > 0 && (
        <div className="bg-studio-850 rounded-lg border border-studio-700 p-4">
          <h4 className="text-xs font-semibold text-studio-300 uppercase tracking-wider mb-2.5">
            Diagnostics Stream
          </h4>
          <div className="space-y-1.5 font-mono text-xs">
            {diagnostics.map((diag, idx) => (
              <div
                key={idx}
                className={`p-2 rounded border flex items-center justify-between ${
                  diag.severity === 'error'
                    ? 'bg-accent-red/10 border-accent-red/30 text-accent-red'
                    : 'bg-studio-800 border-studio-700 text-studio-300'
                }`}
              >
                <span>{diag.message}</span>
                {diag.line && (
                  <span className="text-[11px] text-studio-400">
                    Line {diag.line}:{diag.column}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
