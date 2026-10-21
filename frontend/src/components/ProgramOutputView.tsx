import React, { useState } from 'react';
import { CompilerError } from '../types/compiler';

interface ProgramOutputViewProps {
  output?: number[] | null;
  stdoutText?: string | null;
  executionStatus?: 'success' | 'error' | 'step_limit_exceeded' | null;
  runtimeErrors?: CompilerError[];
  executionSteps?: number | null;
  executionMs?: number;
}

export const ProgramOutputView: React.FC<ProgramOutputViewProps> = ({
  output,
  stdoutText,
  executionStatus,
  runtimeErrors = [],
  executionSteps,
  executionMs,
}) => {
  const [copied, setCopied] = useState(false);

  // Build terminal output string
  let consoleText = '';
  if (executionStatus === 'success') {
    if (stdoutText && stdoutText.trim().length > 0) {
      consoleText = stdoutText.trim();
    } else if (output && output.length > 0) {
      consoleText = output.join('\n');
    } else {
      consoleText = '[Program executed successfully with no output]';
    }
  } else if (executionStatus === 'step_limit_exceeded') {
    consoleText = `[VM Error] Step limit exceeded (${executionSteps} instructions executed). Possible infinite loop detected.`;
  } else if (executionStatus === 'error' || runtimeErrors.length > 0) {
    consoleText = runtimeErrors.map((e) => `[VM Error] ${e.message}`).join('\n') || '[VM Execution Error] Execution halted.';
  } else {
    consoleText = 'Click "Compile & Run" to compile and execute program in the Sudarshan VM.';
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(consoleText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div className="pane-subheading-bar">
        <div className="pane-subheading">8. Expected program output</div>
        <div className="flex items-center gap-2">
          {executionStatus === 'success' && executionSteps !== undefined && executionSteps !== null && (
            <span className="text-xs font-mono text-studio-400">
              {executionSteps} VM steps ({executionMs || 0} ms)
            </span>
          )}
          <button onClick={handleCopy} className="btn-sm btn-ghost">
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="terminal-box">
        <div className="terminal-header">
          <span className="dot red" />
          <span className="dot yellow" />
          <span className="dot green" />
          <span className="terminal-title">sudarshan-vm --run</span>
        </div>
        <div className="terminal-body font-mono text-sm leading-relaxed min-h-[160px]">
          {executionStatus === 'success' ? (
            <span className="text-emerald-400 font-mono whitespace-pre-wrap">{consoleText}</span>
          ) : executionStatus === 'error' || executionStatus === 'step_limit_exceeded' ? (
            <span className="text-red-400 font-mono whitespace-pre-wrap">{consoleText}</span>
          ) : (
            <span className="terminal-muted">{consoleText}</span>
          )}
        </div>
      </div>
    </div>
  );
};
