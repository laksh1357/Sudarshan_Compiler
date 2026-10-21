import React from 'react';
import { Terminal, Cpu, Github, RotateCcw, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

interface HeaderProps {
  status: 'idle' | 'compiling' | 'success' | 'error';
  optimize: boolean;
  onToggleOptimize: () => void;
  onReset: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  optimize,
  onToggleOptimize,
  onReset,
}) => {
  return (
    <header className="h-14 border-b border-studio-600 bg-studio-900 px-4 flex items-center justify-between select-none">
      {/* Brand & Language */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 border border-accent-blue/40 flex items-center justify-center text-accent-blue">
          <Terminal className="w-4 h-4" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm tracking-wide text-white">SUDARSHAN</span>
            <span className="text-xs px-1.5 py-0.5 rounded bg-studio-700 text-studio-300 font-mono">STUDIO</span>
          </div>
          <div className="text-[10px] text-studio-400 font-mono flex items-center gap-1.5">
            <span>Compiler & VM</span>
            <span className="text-studio-600">•</span>
            <span className="text-accent-blue">MiniLang</span>
          </div>
        </div>
      </div>

      {/* Middle Status */}
      <div className="hidden md:flex items-center gap-3">
        {status === 'compiling' && (
          <div className="flex items-center gap-2 text-xs text-accent-blue bg-accent-blue/10 border border-accent-blue/30 px-2.5 py-1 rounded-full">
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Compiling Pipeline...</span>
          </div>
        )}
        {status === 'success' && (
          <div className="flex items-center gap-2 text-xs text-accent-green bg-accent-green/10 border border-accent-green/30 px-2.5 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Compilation Successful</span>
          </div>
        )}
        {status === 'error' && (
          <div className="flex items-center gap-2 text-xs text-accent-red bg-accent-red/10 border border-accent-red/30 px-2.5 py-1 rounded-full">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Compilation Error</span>
          </div>
        )}
        {status === 'idle' && (
          <div className="text-xs text-studio-400 font-mono">Ready to compile</div>
        )}
      </div>

      {/* Actions & Controls */}
      <div className="flex items-center gap-2">
        {/* Optimization Toggle */}
        <button
          onClick={onToggleOptimize}
          title={optimize ? "TAC Optimizer Enabled (Constant Folding & DCE)" : "TAC Optimizer Disabled"}
          className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded border transition-colors ${
            optimize
              ? 'bg-accent-blue/10 border-accent-blue/40 text-accent-blue hover:bg-accent-blue/20'
              : 'bg-studio-800 border-studio-600 text-studio-400 hover:bg-studio-700'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          <span>{optimize ? 'O1 OPT ON' : 'O0 RAW'}</span>
        </button>

        {/* Reset Action */}
        <button
          onClick={onReset}
          title="Reset to default example"
          className="p-1.5 text-studio-400 hover:text-studio-200 hover:bg-studio-800 rounded border border-studio-600 transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* GitHub Link */}
        <a
          href="https://github.com/laksh1357/Sudarshan_Compiler"
          target="_blank"
          rel="noreferrer"
          title="View GitHub Repository"
          className="p-1.5 text-studio-400 hover:text-studio-200 hover:bg-studio-800 rounded border border-studio-600 transition-colors"
        >
          <Github className="w-3.5 h-3.5" />
        </a>
      </div>
    </header>
  );
};
