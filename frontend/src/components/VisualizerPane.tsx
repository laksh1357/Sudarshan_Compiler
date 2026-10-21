import React from 'react';
import { PipelineStage, CompilationResponse } from '../types/compiler';
import { TokenTable } from './TokenTable';
import { ASTViewer } from './ASTViewer';
import { SymbolTableView } from './SymbolTableView';
import { SemanticDiagnosticsView } from './SemanticDiagnosticsView';
import { RawTACViewer } from './RawTACViewer';
import { OptimizedTACViewer } from './OptimizedTACViewer';
import { OptimizationReportView } from './OptimizationReportView';
import { ProgramOutputView } from './ProgramOutputView';

interface VisualizerPaneProps {
  activeStage: PipelineStage;
  onSelectStage: (stage: PipelineStage) => void;
  result: CompilationResponse | null;
}

export const VisualizerPane: React.FC<VisualizerPaneProps> = ({
  activeStage,
  onSelectStage,
  result,
}) => {
  const tabs: Array<{ id: PipelineStage; num: number; label: string }> = [
    { id: 'tokens', num: 1, label: 'Tokens' },
    { id: 'ast', num: 2, label: 'AST Tree' },
    { id: 'symbol-table', num: 3, label: 'Symbol Table' },
    { id: 'semantic', num: 4, label: 'Semantics' },
    { id: 'raw-tac', num: 5, label: 'Raw IR' },
    { id: 'opt-tac', num: 6, label: 'Opt IR' },
    { id: 'optimization', num: 7, label: 'Opt Behavior' },
    { id: 'output', num: 8, label: 'Output' },
  ];

  const semanticPassed =
    result !== null &&
    result.failed_phase !== 'lexical' &&
    result.failed_phase !== 'syntax' &&
    result.failed_phase !== 'semantic';

  return (
    <section className="pane visualizer-pane">
      {/* Tab Bar */}
      <div className="tab-bar">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onSelectStage(tab.id)}
            className={`tab-btn ${activeStage === tab.id ? 'active' : ''}`}
          >
            <span className="tab-badge">{tab.num}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content Container */}
      <div className="tab-content-container">
        {activeStage === 'tokens' && (
          <TokenTable tokens={result?.tokens} />
        )}

        {activeStage === 'ast' && (
          <ASTViewer ast={result?.ast} astText={result?.ast_text} />
        )}

        {activeStage === 'symbol-table' && (
          <SymbolTableView symbolTable={result?.symbol_table} />
        )}

        {activeStage === 'semantic' && (
          <SemanticDiagnosticsView
            diagnostics={result?.semantic_diagnostics || []}
            errors={result?.compilation_errors || []}
            semanticPassed={semanticPassed}
          />
        )}

        {activeStage === 'raw-tac' && (
          <RawTACViewer
            rawTac={result?.raw_tac}
            rawTacText={result?.raw_tac_text}
          />
        )}

        {activeStage === 'opt-tac' && (
          <OptimizedTACViewer
            optimizedTac={result?.optimized_tac}
            optimizedTacText={result?.optimized_tac_text}
            stats={result?.optimization_stats}
          />
        )}

        {activeStage === 'optimization' && (
          <OptimizationReportView
            report={result?.optimization_report || []}
            stats={result?.optimization_stats}
          />
        )}

        {activeStage === 'output' && (
          <ProgramOutputView
            output={result?.program_output}
            stdoutText={result?.stdout_text}
            executionStatus={result?.execution_status}
            runtimeErrors={result?.runtime_errors}
            executionSteps={result?.execution_steps}
            executionMs={result?.timing?.execution_ms}
          />
        )}
      </div>
    </section>
  );
};
