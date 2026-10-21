/**
 * API Client for Sudarshan Compiler Studio.
 */

import {
  CompilationResponse,
  ExampleProgram,
  HealthInfo
} from '../types/compiler';

// Read API base URL from Vite environment or default to relative path
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export async function fetchHealth(): Promise<HealthInfo> {
  const resp = await fetch(`${API_BASE_URL}/api/health`);
  if (!resp.ok) {
    throw new Error(`Failed to fetch health status: ${resp.statusText}`);
  }
  return resp.json();
}

export async function fetchExamples(): Promise<ExampleProgram[]> {
  const resp = await fetch(`${API_BASE_URL}/api/examples`);
  if (!resp.ok) {
    throw new Error(`Failed to load compiler examples: ${resp.statusText}`);
  }
  return resp.json();
}

export async function compileCode(
  sourceCode: string,
  optimize: boolean = true,
  maxSteps: number = 100000
): Promise<CompilationResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/compile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_code: sourceCode,
      optimize,
      max_steps: maxSteps,
    }),
  });

  if (!resp.ok && resp.status !== 400 && resp.status !== 413) {
    throw new Error(`Compilation request failed: ${resp.statusText}`);
  }
  return resp.json();
}

export async function compileAndRunCode(
  sourceCode: string,
  optimize: boolean = true,
  maxSteps: number = 100000
): Promise<CompilationResponse> {
  const resp = await fetch(`${API_BASE_URL}/api/compile-run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_code: sourceCode,
      optimize,
      max_steps: maxSteps,
    }),
  });

  if (!resp.ok && resp.status !== 400 && resp.status !== 413) {
    throw new Error(`Execution request failed: ${resp.statusText}`);
  }
  return resp.json();
}
