import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { EditorToolbar } from './components/EditorToolbar';
import { SourceEditor } from './components/SourceEditor';
import { PipelineNav } from './components/PipelineNav';
import { TokenTable } from './components/TokenTable';
import { ASTViewer } from './components/ASTViewer';
import { SymbolTableView } from './components/SymbolTableView';
import { SemanticDiagnosticsView } from './components/SemanticDiagnosticsView';
import { RawTACViewer } from './components/RawTACViewer';
import { OptimizedTACViewer } from './components/OptimizedTACViewer';
import { OptimizationReportView } from './components/OptimizationReportView';
import { ProgramOutputView } from './components/ProgramOutputView';
import { ErrorBanner } from './components/ErrorBanner';

import {
  ExampleProgram,
  PipelineStage,
  CompilationResponse,
  CompilerError,
} from './types/compiler';
import { fetchExamples, compileCode, compileAndRunCode } from './api/client';

const INITIAL_CODE = `// Valid MiniLang Test Program
// Demonstrates: variable declarations, assignments, arithmetic, while loop, if/else, and print.
// Expected Output:
// 15
// 115

int sum = 0;
int i = 1;

while (i <= 5) {
    sum = sum + i;
    i = i + 1;
}

print(sum);

if (sum >= 15) {
    int bonus = 100;
    print(sum + bonus);
} else {
    print(0);
}
`;

export const App: React.FC = () => {
  const [examples, setExamples] = useState<ExampleProgram[]>([]);
  const [selectedExampleId, setSelectedExampleId] = useState<string>('valid-program');
  const [sourceCode, setSourceCode] = useState<string>(() => {
    return localStorage.getItem('sudarshan_source_code') || INITIAL_CODE;
  });
  const [activeStage, setActiveStage] = useState<PipelineStage>('output');
  const [optimize, setOptimize] = useState<boolean>(true);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [result, setResult] = useState<CompilationResponse | null>(null);
  const [status, setStatus] = useState<'idle' | 'compiling' | 'success' | 'error'>('idle');

  // Load example list on initial mount
  useEffect(() => {
    async function loadData() {
      try {
        const exList = await fetchExamples();
        setExamples(exList);
      } catch (err) {
        console.warn('Could not load examples from server:', err);
      }
    }
    loadData();
  }, []);

  // Persist code to localStorage
  useEffect(() => {
    localStorage.setItem('sudarshan_source_code', sourceCode);
  }, [sourceCode]);

  // Initial compilation on page load
  useEffect(() => {
    handleCompileAndRun();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle Compile (IR generation only)
  const handleCompile = async () => {
    setIsCompiling(true);
    setStatus('compiling');
    try {
      const res = await compileCode(sourceCode, optimize);
      setResult(res);
      setStatus(res.success ? 'success' : 'error');

      // If compilation failed, route to the failing stage
      if (!res.success && res.failed_phase) {
        routeToFailedPhase(res.failed_phase);
      } else if (activeStage === 'output') {
        setActiveStage('opt-tac');
      }
    } catch (err: any) {
      setStatus('error');
      console.error(err);
    } finally {
      setIsCompiling(false);
    }
  };

  // Handle Compile & Run (all phases through VM)
  const handleCompileAndRun = async () => {
    setIsCompiling(true);
    setStatus('compiling');
    try {
      const res = await compileAndRunCode(sourceCode, optimize);
      setResult(res);
      setStatus(res.success && res.execution_status === 'success' ? 'success' : 'error');

      if (!res.success && res.failed_phase) {
        routeToFailedPhase(res.failed_phase);
      } else {
        setActiveStage('output');
      }
    } catch (err: any) {
      setStatus('error');
      console.error(err);
    } finally {
      setIsCompiling(false);
    }
  };

  const routeToFailedPhase = (phase: string) => {
    switch (phase) {
      case 'lexical':
        setActiveStage('tokens');
        break;
      case 'syntax':
        setActiveStage('ast');
        break;
      case 'semantic':
        setActiveStage('semantic');
        break;
      case 'tac':
        setActiveStage('raw-tac');
        break;
      case 'optimization':
        setActiveStage('opt-tac');
        break;
      default:
        setActiveStage('output');
    }
  };

  const handleSelectExample = (example: ExampleProgram) => {
    setSelectedExampleId(example.id);
    setSourceCode(example.source_code);
    setResult(null);
    setStatus('idle');
  };

  const handleReset = () => {
    const found = examples.find((ex) => ex.id === selectedExampleId);
    if (found) {
      setSourceCode(found.source_code);
    } else {
      setSourceCode(INITIAL_CODE);
    }
  };

  const handleClear = () => {
    setSourceCode('');
    setResult(null);
    setStatus('idle');
  };

  const handleToggleOptimize = () => {
    setOptimize(!optimize);
  };

  // Extract all current compilation errors
  const currentErrors: CompilerError[] = [
    ...(result?.compilation_errors || []),
    ...(result?.runtime_errors || []),
  ];

  return (
    <div className="flex flex-col h-screen w-screen bg-studio-950 text-studio-200 overflow-hidden">
      {/* Top Header */}
      <Header
        status={status}
        optimize={optimize}
        onToggleOptimize={handleToggleOptimize}
        onReset={handleReset}
      />

      {/* Main Toolbar */}
      <EditorToolbar
        examples={examples}
        selectedExampleId={selectedExampleId}
        onSelectExample={handleSelectExample}
        onCompile={handleCompile}
        onCompileAndRun={handleCompileAndRun}
        onClear={handleClear}
        onReset={handleReset}
        sourceCode={sourceCode}
        isCompiling={isCompiling}
        timing={result?.timing}
      />

      {/* Main Workspace (Split Grid) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 overflow-hidden">
        {/* Left Column: Monaco Source Code Editor */}
        <div className="flex flex-col border-r border-studio-600 h-full overflow-hidden">
          <div className="h-8 px-3 bg-studio-850 border-b border-studio-700 flex items-center justify-between text-xs font-mono text-studio-400 select-none">
            <span className="flex items-center gap-1.5 text-studio-300 font-semibold">
              <span>main.mini</span>
              <span className="text-[10px] text-accent-blue bg-accent-blue/10 px-1.5 py-0.2 rounded border border-accent-blue/30">
                Sudarshan Source
              </span>
            </span>
            <span className="text-[11px] text-studio-500">UTF-8 • LR(1) BNF</span>
          </div>

          <div className="flex-1 overflow-hidden relative">
            <SourceEditor
              value={sourceCode}
              onChange={setSourceCode}
              errors={currentErrors}
            />
          </div>

          {/* Error Banner at bottom of editor if compilation failed */}
          {result?.compilation_errors && result.compilation_errors.length > 0 && (
            <div className="max-h-48 overflow-auto border-t border-accent-red/30 bg-studio-950">
              {result.compilation_errors.map((err, idx) => (
                <ErrorBanner key={idx} error={err} />
              ))}
            </div>
          )}
        </div>

        {/* Right Column: 8-Phase Compiler Pipeline */}
        <div className="flex flex-col h-full overflow-hidden bg-studio-900">
          {/* Stepper Navigation */}
          <PipelineNav
            activeStage={activeStage}
            onSelectStage={setActiveStage}
            result={result}
          />

          {/* Active Stage View Panel */}
          <div className="flex-1 overflow-hidden relative">
            {activeStage === 'tokens' && (
              <TokenTable tokens={result?.tokens} />
            )}

            {activeStage === 'ast' && (
              <ASTViewer
                ast={result?.ast}
                astText={result?.ast_text}
                astDot={result?.ast_dot}
              />
            )}

            {activeStage === 'symbol-table' && (
              <SymbolTableView symbolTable={result?.symbol_table} />
            )}

            {activeStage === 'semantic' && (
              <SemanticDiagnosticsView
                diagnostics={result?.semantic_diagnostics || []}
                errors={result?.compilation_errors || []}
                success={result?.success || false}
              />
            )}

            {activeStage === 'raw-tac' && (
              <RawTACViewer
                instructions={result?.raw_tac}
                rawText={result?.raw_tac_text}
              />
            )}

            {activeStage === 'opt-tac' && (
              <OptimizedTACViewer
                rawInstructions={result?.raw_tac}
                optInstructions={result?.optimized_tac}
                optText={result?.optimized_tac_text}
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
                status={result?.execution_status}
                runtimeErrors={result?.runtime_errors}
                executionSteps={result?.execution_steps}
                executionMs={result?.timing?.execution_ms}
                onRerun={handleCompileAndRun}
                isCompiling={isCompiling}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
