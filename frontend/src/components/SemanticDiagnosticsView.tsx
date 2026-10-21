import React, { useState } from 'react';
import { SemanticDiagnostic, CompilerError } from '../types/compiler';

interface SemanticDiagnosticsViewProps {
  diagnostics: SemanticDiagnostic[];
  errors: CompilerError[];
  semanticPassed: boolean;
}

export const SemanticDiagnosticsView: React.FC<SemanticDiagnosticsViewProps> = ({
  diagnostics,
  errors,
  semanticPassed,
}) => {
  const [copied, setCopied] = useState(false);

  const semanticErrors = errors.filter((e) => e.phase === 'semantic');
  const isSuccess = semanticPassed && semanticErrors.length === 0;

  // Checks checklist items
  const checks = isSuccess
    ? [
        'Type compatibility checked: variable assignments and binary operations are type-safe.',
        'Identifier resolution verified: all referenced variables are declared in accessible scopes.',
        'Declaration uniqueness verified: no illegal variable re-declarations within the same scope.',
        'Control flow conditions validated: loop and branch guards evaluate correctly.',
      ]
    : semanticErrors.map((e) => `Semantic check failed: ${e.message}`);

  const rawText = isSuccess
    ? `Semantic analysis: SUCCESS\n\nChecks passed:\n${checks.map((c) => `- ${c}`).join('\n')}\n\nAll static semantic constraints satisfied.`
    : `Semantic analysis: FAILED\n\nErrors encountered:\n${semanticErrors.map((e) => `- [Line ${e.line || '?'}:${e.column || '?'}] ${e.message}`).join('\n')}`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(rawText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">4. Expected semantic-analysis result</div>
        <button onClick={handleCopy} className="btn-sm btn-ghost">
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>

      {/* Status Banner */}
      <div className={`status-banner ${isSuccess ? 'success' : 'error'}`}>
        <span className="status-icon">{isSuccess ? '✓' : '✗'}</span>
        <span>
          {isSuccess ? 'Semantic analysis: SUCCESS' : 'Semantic analysis: FAILED'}
        </span>
      </div>

      {/* Checks List */}
      <div className="checks-wrapper">
        <div className="checks-title">
          {isSuccess ? 'Checks passed:' : 'Checks failed:'}
        </div>
        <ul className="checks-list">
          {checks.map((check, idx) => (
            <li key={idx}>
              <span className={`check-icon ${isSuccess ? '' : 'error'}`}>
                {isSuccess ? '✓' : '✗'}
              </span>
              <span>{check}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Code Box Wrapper */}
      <div className="code-box-wrapper">
        <div className="code-box-header">
          <span className="code-box-title">text</span>
          <button className="copy-icon-btn" onClick={handleCopy} title="Copy text">
            {copied ? '✓' : '📋'}
          </button>
        </div>
        <pre className="code-view font-mono text-xs text-studio-300">{rawText}</pre>
      </div>
    </div>
  );
};
