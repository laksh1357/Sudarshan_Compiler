import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ErrorBanner } from './components/ErrorBanner';
import { SourceEditor } from './components/SourceEditor';
import { VisualizerPane } from './components/VisualizerPane';

import {
  ExampleProgram,
  PipelineStage,
  CompilationResponse,
  CompilerError,
} from './types/compiler';
import { fetchExamples, compileAndRunCode } from './api/client';

const INITIAL_CODE = `// Valid Sudarshan Program
// Demonstrates: variable declarations, while loop, conditional branching, and print.
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
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [result, setResult] = useState<CompilationResponse | null>(null);
  const [errors, setErrors] = useState<CompilerError[]>([]);

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

  // Persist source code to localStorage
  useEffect(() => {
    localStorage.setItem('sudarshan_source_code', sourceCode);
  }, [sourceCode]);

  // Initial compilation on page load
  useEffect(() => {
    handleCompileAndRun();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle Compile & Run (all phases through VM)
  const handleCompileAndRun = async () => {
    setIsCompiling(true);
    setErrors([]);
    try {
      const res = await compileAndRunCode(sourceCode, true);
      setResult(res);

      const errs: CompilerError[] = [
        ...(res.compilation_errors || []),
        ...(res.runtime_errors || []),
      ];
      setErrors(errs);

      // If compilation failed, navigate to the failing phase tab
      if (!res.success && res.failed_phase) {
        routeToFailedPhase(res.failed_phase);
      } else {
        setActiveStage('output');
      }
    } catch (err: any) {
      console.error(err);
      setErrors([
        {
          phase: 'network',
          error_type: 'ConnectionError',
          message: err.message || 'Failed to reach backend compilation server.',
        },
      ]);
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

  const handleSelectExampleId = (id: string) => {
    setSelectedExampleId(id);
    if (id === 'custom') return;
    const found = examples.find((ex) => ex.id === id);
    if (found) {
      setSourceCode(found.source_code);
      setResult(null);
      setErrors([]);
    }
  };

  const handleClear = () => {
    setSourceCode('');
    setSelectedExampleId('custom');
    setResult(null);
    setErrors([]);
  };

  const handleDismissErrors = () => {
    setErrors([]);
  };

  return (
    <div className="app-container">
      {/* Top Navigation Header */}
      <Header
        activeStage={activeStage}
        onSelectStage={setActiveStage}
        examples={examples}
        selectedExampleId={selectedExampleId}
        onSelectExampleId={handleSelectExampleId}
        onCompileAndRun={handleCompileAndRun}
        isCompiling={isCompiling}
      />

      {/* Error Notification Banner */}
      <ErrorBanner errors={errors} onDismiss={handleDismissErrors} />

      {/* Main Workspace Split Grid */}
      <main className="workspace-grid">
        {/* Left Side: Source Code Editor */}
        <SourceEditor
          value={sourceCode}
          onChange={(val) => {
            setSourceCode(val);
            if (selectedExampleId !== 'custom') {
              setSelectedExampleId('custom');
            }
          }}
          onClear={handleClear}
        />

        {/* Right Side: Compilation Output Visualizer Tabs */}
        <VisualizerPane
          activeStage={activeStage}
          onSelectStage={setActiveStage}
          result={result}
        />
      </main>
    </div>
  );
};

export default App;
