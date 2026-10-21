import React from 'react';
import { PipelineStage, ExampleProgram } from '../types/compiler';

interface HeaderProps {
  activeStage: PipelineStage;
  onSelectStage: (stage: PipelineStage) => void;
  examples: ExampleProgram[];
  selectedExampleId: string;
  onSelectExampleId: (id: string) => void;
  onCompileAndRun: () => void;
  isCompiling: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  activeStage,
  onSelectStage,
  examples,
  selectedExampleId,
  onSelectExampleId,
  onCompileAndRun,
  isCompiling,
}) => {
  return (
    <header className="navbar">
      {/* Brand */}
      <div className="brand">
        <div className="logo-icon">⚡</div>
        <div className="logo-text">
          <h1>Sudarshan Studio</h1>
          <span className="sub-title">Sudarshan Language Compiler &amp; TAC Engine</span>
        </div>
      </div>

      {/* Compiler Pipeline Tracker */}
      <div className="compiler-pipeline hidden md:flex">
        <div
          className={`pipeline-step ${activeStage === 'tokens' ? 'active' : ''}`}
          onClick={() => onSelectStage('tokens')}
          title="Inspect Lexical Tokens"
        >
          1. Tokens
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'ast' ? 'active' : ''}`}
          onClick={() => onSelectStage('ast')}
          title="Inspect Abstract Syntax Tree"
        >
          2. AST
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'symbol-table' ? 'active' : ''}`}
          onClick={() => onSelectStage('symbol-table')}
          title="Inspect Scoped Symbol Table"
        >
          3. Symbol Table
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'semantic' ? 'active' : ''}`}
          onClick={() => onSelectStage('semantic')}
          title="Inspect Semantic Diagnostics"
        >
          4. Semantics
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'raw-tac' ? 'active' : ''}`}
          onClick={() => onSelectStage('raw-tac')}
          title="Inspect Raw TAC (Intermediate Code)"
        >
          5. Raw TAC
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'opt-tac' ? 'active' : ''}`}
          onClick={() => onSelectStage('opt-tac')}
          title="Inspect Optimized TAC"
        >
          6. Opt TAC
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'optimization' ? 'active' : ''}`}
          onClick={() => onSelectStage('optimization')}
          title="Inspect Optimizer Behavior & Transformations"
        >
          7. Opt Behavior
        </div>
        <div className="pipeline-arrow">→</div>

        <div
          className={`pipeline-step ${activeStage === 'output' ? 'active' : ''}`}
          onClick={() => onSelectStage('output')}
          title="Inspect Program Execution Output"
        >
          8. Output
        </div>
      </div>

      {/* Header Actions */}
      <div className="header-actions">
        <div className="preset-group">
          <label htmlFor="preset-select" className="hidden sm:inline">Samples:</label>
          <select
            id="preset-select"
            className="preset-dropdown"
            value={selectedExampleId}
            onChange={(e) => onSelectExampleId(e.target.value)}
          >
            {examples.map((ex) => (
              <option key={ex.id} value={ex.id}>
                {ex.filename} ({ex.name})
              </option>
            ))}
            <option value="custom">✏️ Custom Program</option>
          </select>
        </div>

        <button
          id="run-btn"
          className="btn btn-primary"
          onClick={onCompileAndRun}
          disabled={isCompiling}
          title="Compile source and run in Sudarshan VM"
        >
          {isCompiling ? (
            <>
              <span className="btn-icon animate-spin">⏳</span> Compiling...
            </>
          ) : (
            <>
              <span className="btn-icon">▶</span> Compile &amp; Run
            </>
          )}
        </button>
      </div>
    </header>
  );
};
