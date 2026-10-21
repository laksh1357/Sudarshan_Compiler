import React from 'react';
import {
  ListFilter,
  Network,
  Table2,
  ShieldCheck,
  Binary,
  Zap,
  Sparkles,
  Terminal,
  Check,
  AlertCircle
} from 'lucide-react';
import { PipelineStage, CompilationResponse } from '../types/compiler';

interface PipelineNavProps {
  activeStage: PipelineStage;
  onSelectStage: (stage: PipelineStage) => void;
  result: CompilationResponse | null;
}

interface StageConfig {
  id: PipelineStage;
  number: number;
  label: string;
  shortLabel: string;
  icon: React.ReactNode;
  getStatus: (res: CompilationResponse | null) => 'success' | 'error' | 'pending' | 'none';
}

const STAGES: StageConfig[] = [
  {
    id: 'tokens',
    number: 1,
    label: 'Tokens',
    shortLabel: 'Tokens',
    icon: <ListFilter className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'lexical') return 'error';
      return res.tokens ? 'success' : 'none';
    },
  },
  {
    id: 'ast',
    number: 2,
    label: 'AST',
    shortLabel: 'AST',
    icon: <Network className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'syntax') return 'error';
      return res.ast ? 'success' : 'none';
    },
  },
  {
    id: 'symbol-table',
    number: 3,
    label: 'Symbol Table',
    shortLabel: 'Symbols',
    icon: <Table2 className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'semantic') return 'error';
      return res.symbol_table ? 'success' : 'none';
    },
  },
  {
    id: 'semantic',
    number: 4,
    label: 'Semantic Analysis',
    shortLabel: 'Semantic',
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'semantic') return 'error';
      return res.symbol_table ? 'success' : 'none';
    },
  },
  {
    id: 'raw-tac',
    number: 5,
    label: 'Raw TAC',
    shortLabel: 'Raw IR',
    icon: <Binary className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'tac') return 'error';
      return res.raw_tac ? 'success' : 'none';
    },
  },
  {
    id: 'opt-tac',
    number: 6,
    label: 'Optimized TAC',
    shortLabel: 'Opt IR',
    icon: <Zap className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      if (res.failed_phase === 'optimization') return 'error';
      return res.optimized_tac ? 'success' : 'none';
    },
  },
  {
    id: 'optimization',
    number: 7,
    label: 'Optimization Analysis',
    shortLabel: 'Analysis',
    icon: <Sparkles className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res) return 'none';
      return res.optimization_report ? 'success' : 'none';
    },
  },
  {
    id: 'output',
    number: 8,
    label: 'Program Output',
    shortLabel: 'Output',
    icon: <Terminal className="w-3.5 h-3.5" />,
    getStatus: (res) => {
      if (!res || !res.execution_status) return 'none';
      if (res.execution_status === 'error' || res.execution_status === 'step_limit_exceeded') return 'error';
      return 'success';
    },
  },
];

export const PipelineNav: React.FC<PipelineNavProps> = ({
  activeStage,
  onSelectStage,
  result,
}) => {
  return (
    <div className="h-11 border-b border-studio-600 bg-studio-900 px-2 flex items-center gap-1 select-none overflow-x-auto no-scrollbar">
      {STAGES.map((stage) => {
        const isActive = activeStage === stage.id;
        const status = stage.getStatus(result);

        return (
          <button
            key={stage.id}
            onClick={() => onSelectStage(stage.id)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium transition-all whitespace-nowrap ${
              isActive
                ? 'bg-studio-700 text-white border border-studio-500 shadow-sm'
                : 'text-studio-400 hover:text-studio-200 hover:bg-studio-800'
            }`}
          >
            {/* Step Icon */}
            <span
              className={`${
                isActive ? 'text-accent-blue' : 'text-studio-500'
              }`}
            >
              {stage.icon}
            </span>

            {/* Label */}
            <span>
              <span className="opacity-50 mr-1">{stage.number}.</span>
              {stage.shortLabel}
            </span>

            {/* Status Indicator */}
            {status === 'success' && (
              <span className="w-3.5 h-3.5 rounded-full bg-accent-green/20 text-accent-green flex items-center justify-center">
                <Check className="w-2.5 h-2.5" />
              </span>
            )}
            {status === 'error' && (
              <span className="w-3.5 h-3.5 rounded-full bg-accent-red/20 text-accent-red flex items-center justify-center">
                <AlertCircle className="w-2.5 h-2.5" />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
