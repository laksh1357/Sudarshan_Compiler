import React, { useState } from 'react';
import { Sparkles, ArrowRight, CheckCircle2, TrendingDown, Layers, HelpCircle } from 'lucide-react';
import { OptimizationRecord, OptimizationStats } from '../types/compiler';

interface OptimizationReportViewProps {
  report: OptimizationRecord[];
  stats?: OptimizationStats | null;
}

export const OptimizationReportView: React.FC<OptimizationReportViewProps> = ({
  report,
  stats,
}) => {
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  if (!report || report.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-studio-400 p-6">
        <Sparkles className="w-8 h-8 text-studio-600 mb-2" />
        <p className="text-sm font-medium">No Optimizations Applied</p>
        <p className="text-xs text-studio-500 mt-1 max-w-sm text-center">
          The optimizer analyzed the intermediate code, but no constant folding, algebraic identities, or dead-code elimination opportunities were detected.
        </p>
      </div>
    );
  }

  // Categories
  const categories = Array.from(new Set(report.map((r) => r.category)));

  const filteredReport = filterCategory === 'ALL'
    ? report
    : report.filter((r) => r.category === filterCategory);

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'constant_folding':
        return 'bg-accent-blue/10 text-accent-blue border-accent-blue/30';
      case 'constant_propagation':
        return 'bg-accent-purple/10 text-accent-purple border-accent-purple/30';
      case 'algebraic':
        return 'bg-accent-green/10 text-accent-green border-accent-green/30';
      case 'dead_code':
        return 'bg-accent-red/10 text-accent-red border-accent-red/30';
      case 'branch_simplification':
        return 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/30';
      default:
        return 'bg-studio-700 text-studio-300 border-studio-600';
    }
  };

  return (
    <div className="h-full flex flex-col bg-studio-900 overflow-auto p-4 gap-4">
      {/* Top Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <Sparkles className="w-4 h-4 text-accent-yellow" />
            <span>Transformations</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">{report.length}</div>
        </div>

        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <TrendingDown className="w-4 h-4 text-accent-green" />
            <span>IR Instruction Reduction</span>
          </div>
          <div className="text-xl font-bold font-mono text-accent-green">
            {stats ? `-${stats.reduction_percentage}%` : '0%'}
          </div>
        </div>

        <div className="p-3 bg-studio-850 rounded-lg border border-studio-700">
          <div className="flex items-center gap-2 text-studio-400 text-xs font-medium mb-1">
            <Layers className="w-4 h-4 text-accent-purple" />
            <span>Active Optimization Passes</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">{categories.length}</div>
        </div>
      </div>

      {/* Filter Chips */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <button
          onClick={() => setFilterCategory('ALL')}
          className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
            filterCategory === 'ALL'
              ? 'bg-studio-700 text-white border border-studio-500'
              : 'bg-studio-800 text-studio-400 hover:text-studio-200 border border-studio-700'
          }`}
        >
          All ({report.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setFilterCategory(cat)}
            className={`px-2.5 py-1 rounded text-xs font-medium uppercase font-mono transition-colors ${
              filterCategory === cat
                ? 'bg-studio-700 text-white border border-studio-500'
                : 'bg-studio-800 text-studio-400 hover:text-studio-200 border border-studio-700'
            }`}
          >
            {cat.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Transformations List */}
      <div className="space-y-3">
        {filteredReport.map((rec, idx) => (
          <div
            key={idx}
            className="p-3.5 bg-studio-850 rounded-lg border border-studio-700 hover:border-studio-600 transition-colors"
          >
            {/* Header */}
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="font-semibold text-xs text-white flex items-center gap-2">
                <span className="text-studio-500 font-mono text-[11px]">#{idx + 1}</span>
                {rec.pass_name}
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold border ${getCategoryBadge(rec.category)}`}>
                {rec.category.replace('_', ' ')}
              </span>
            </div>

            {/* Instruction Transformation Display */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 my-2 font-mono text-xs">
              <div className="p-2 bg-studio-900 rounded border border-studio-750 text-studio-400">
                <span className="text-[10px] uppercase text-studio-500 block mb-1">Before:</span>
                <code className="text-accent-red/90">{rec.original}</code>
              </div>

              <div className="p-2 bg-studio-900 rounded border border-accent-green/20 text-accent-green">
                <span className="text-[10px] uppercase text-studio-500 block mb-1">After:</span>
                <code className="font-semibold">{rec.transformed}</code>
              </div>
            </div>

            {/* Reason */}
            <div className="text-xs text-studio-400 flex items-start gap-1.5 mt-2">
              <HelpCircle className="w-3.5 h-3.5 text-accent-blue shrink-0 mt-0.5" />
              <span>{rec.reason}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
