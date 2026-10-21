import React from 'react';
import { Terminal, CheckCircle2, AlertOctagon, Clock, Activity, RotateCcw } from 'lucide-react';
import { CompilerError } from '../types/compiler';

interface ProgramOutputViewProps {
  output?: number[] | null;
  stdoutText?: string | null;
  status?: 'success' | 'error' | 'step_limit_exceeded' | null;
  runtimeErrors?: CompilerError[];
  executionSteps?: number | null;
  executionMs?: number;
  onRerun: () => void;
  isCompiling: boolean;
}

export const ProgramOutputView: React.FC<ProgramOutputViewProps> = ({
  output,
  stdoutText,
  status,
  runtimeErrors = [],
  executionSteps,
  executionMs,
  onRerun,
  isCompiling,
}) => {
  if (!status) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Terminal className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">Program Not Yet Executed</p>
        <p className="text-xs text-studio-500 mt-1 max-w-sm text-center">
          Click <strong>Compile & Run</strong> in the toolbar to execute your code through the Sudarshan Virtual Machine.
        </p>
      </div>
    );
  }

  const isSuccess = status === 'success';

  return (
    <div className="h-full flex flex-col bg-studio-950 font-mono text-xs">
      {/* Terminal Title Bar */}
      <div className="px-3 py-2 bg-studio-900 border-b border-studio-700 flex items-center justify-between select-none">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-accent-red/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-accent-yellow/80 inline-block" />
            <span className="w-2.5 h-2.5 rounded-full bg-accent-green/80 inline-block" />
          </div>
          <span className="text-studio-400 text-[11px] ml-2">sudarshan-vm — interactive interpreter</span>
        </div>

        {/* Execution Metrics */}
        <div className="flex items-center gap-3 text-[11px]">
          {executionSteps !== null && executionSteps !== undefined && (
            <div className="flex items-center gap-1 text-studio-400">
              <Activity className="w-3 h-3 text-accent-blue" />
              <span>{executionSteps} VM steps</span>
            </div>
          )}

          {executionMs !== undefined && (
            <div className="flex items-center gap-1 text-studio-400">
              <Clock className="w-3 h-3 text-accent-green" />
              <span>{executionMs.toFixed(2)} ms</span>
            </div>
          )}

          <button
            onClick={onRerun}
            disabled={isCompiling}
            title="Re-run program in Virtual Machine"
            className="flex items-center gap-1 text-studio-400 hover:text-studio-200 bg-studio-800 px-2 py-0.5 rounded border border-studio-700 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Re-run</span>
          </button>
        </div>
      </div>

      {/* Terminal Console Body */}
      <div className="flex-1 overflow-auto p-4 space-y-3 font-mono text-studio-200 select-text">
        <div className="text-studio-500 text-[11px]">
          $ sudarshan-vm --exec-tac
        </div>

        {/* Printed Outputs */}
        {output && output.length > 0 ? (
          <div className="space-y-1">
            {output.map((val, idx) => (
              <div key={idx} className="flex items-baseline gap-2">
                <span className="text-studio-600 select-none text-[10px]">out:</span>
                <span className="text-white font-bold">{val}</span>
              </div>
            ))}
          </div>
        ) : (
          !runtimeErrors.length && (
            <div className="text-studio-500 italic">
              (Program executed with 0 print statements. Add `print(val);` to produce console output.)
            </div>
          )
        )}

        {/* Runtime Errors */}
        {runtimeErrors.map((err, idx) => (
          <div
            key={idx}
            className="p-3 bg-accent-red/10 border border-accent-red/30 rounded text-accent-red space-y-1 mt-2"
          >
            <div className="flex items-center gap-2 font-bold">
              <AlertOctagon className="w-4 h-4 shrink-0" />
              <span>RUNTIME ERROR: {err.error_type}</span>
            </div>
            <p className="text-xs text-studio-200 pl-6">{err.message}</p>
          </div>
        ))}

        {/* Exit Status Footer */}
        <div className="pt-4 border-t border-studio-850 flex items-center gap-2 text-[11px]">
          {isSuccess ? (
            <div className="flex items-center gap-1.5 text-accent-green">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Process finished with exit code 0 (SUCCESS)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-accent-red">
              <AlertOctagon className="w-3.5 h-3.5" />
              <span>Process terminated with runtime error (EXIT 1)</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
