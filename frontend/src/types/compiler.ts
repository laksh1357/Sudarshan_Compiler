/**
 * TypeScript Type Definitions for Sudarshan Compiler Studio.
 */

export interface TokenItem {
  type: string;
  value: any;
  line: number;
  column: number;
}

export interface ASTNodeData {
  id: string;
  type: string;
  label: string;
  line?: number;
  column?: number;
  details: Record<string, any>;
  relation?: string;
  children: ASTNodeData[];
}

export interface SymbolItem {
  name: string;
  type_name: string;
  line?: number;
  column?: number;
  scope_level: number;
}

export interface ScopeItem {
  scope_level: number;
  symbols: SymbolItem[];
}

export interface SymbolTableData {
  scopes: ScopeItem[];
  symbols: SymbolItem[];
}

export interface SemanticDiagnostic {
  severity: 'info' | 'warning' | 'error';
  message: string;
  line?: number;
  column?: number;
}

export interface TACInstructionItem {
  index: number;
  op: string;
  arg1?: any;
  arg2?: any;
  result?: any;
  text: string;
}

export interface OptimizationRecord {
  pass_name: string;
  original: string;
  transformed: string;
  reason: string;
  category: string;
}

export interface OptimizationStats {
  original_count: number;
  optimized_count: number;
  reduction_percentage: number;
  transformations_count: number;
}

export interface CompilerError {
  phase: string;
  error_type: string;
  message: string;
  line?: number;
  column?: number;
  source_context?: string;
}

export interface TimingData {
  lexical_ms: number;
  syntax_ms: number;
  semantic_ms: number;
  tac_ms: number;
  optimization_ms: number;
  execution_ms: number;
  total_ms: number;
}

export interface CompilationResponse {
  success: boolean;
  failed_phase?: string | null;
  tokens?: TokenItem[] | null;
  ast?: ASTNodeData | null;
  ast_text?: string | null;
  ast_dot?: string | null;
  symbol_table?: SymbolTableData | null;
  semantic_diagnostics: SemanticDiagnostic[];
  raw_tac?: TACInstructionItem[] | null;
  raw_tac_text?: string | null;
  optimized_tac?: TACInstructionItem[] | null;
  optimized_tac_text?: string | null;
  optimization_report: OptimizationRecord[];
  optimization_stats?: OptimizationStats | null;
  compilation_errors: CompilerError[];
  timing: TimingData;

  execution_status?: 'success' | 'error' | 'step_limit_exceeded' | null;
  program_output?: number[] | null;
  stdout_text?: string | null;
  runtime_errors: CompilerError[];
  execution_steps?: number | null;
}

export interface ExampleProgram {
  id: string;
  name: string;
  category: string;
  description: string;
  filename: string;
  source_code: string;
  expected_output?: string;
}

export interface HealthInfo {
  status: string;
  name: string;
  version: string;
  compiler: string;
  supported_phases: string[];
}

export type PipelineStage = 
  | 'tokens'
  | 'ast'
  | 'symbol-table'
  | 'semantic'
  | 'raw-tac'
  | 'opt-tac'
  | 'optimization'
  | 'output';
