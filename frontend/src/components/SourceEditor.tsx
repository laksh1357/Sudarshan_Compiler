import React, { useRef } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';
import { CompilerError } from '../types/compiler';

interface SourceEditorProps {
  value: string;
  onChange: (value: string) => void;
  errors: CompilerError[];
}

export const SourceEditor: React.FC<SourceEditorProps> = ({
  value,
  onChange,
  errors,
}) => {
  const monacoRef = useRef<Monaco | null>(null);
  const editorRef = useRef<any>(null);

  const handleEditorWillMount = (monaco: Monaco) => {
    monacoRef.current = monaco;

    // Register Sudarshan language
    if (!monaco.languages.getLanguages().some((l: any) => l.id === 'sudarshan')) {
      monaco.languages.register({ id: 'sudarshan' });

      monaco.languages.setMonarchTokensProvider('sudarshan', {
        keywords: ['int', 'if', 'else', 'while', 'print'],
        operators: ['=', '==', '!=', '<', '>', '<=', '>=', '+', '-', '*', '/'],
        symbols: /[=><!~?:&|+\-*\/\^%]+/,

        tokenizer: {
          root: [
            // Keywords
            [
              /[a-zA-Z_]\w*/,
              {
                cases: {
                  '@keywords': 'keyword',
                  '@default': 'identifier',
                },
              },
            ],

            // Whitespace & Comments
            { include: '@whitespace' },

            // Numbers
            [/\d+/, 'number'],

            // Delimiters and operators
            [/[{}()\[\]]/, '@brackets'],
            [
              /@symbols/,
              {
                cases: {
                  '@operators': 'operator',
                  '@default': '',
                },
              },
            ],
            [/;/, 'delimiter'],
          ],

          whitespace: [
            [/[ \t\r\n]+/, 'white'],
            [/\/\/.*$/, 'comment'],
          ],
        },
      });

      // Define Sudarshan Dark Theme
      monaco.editor.defineTheme('sudarshan-dark', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token: 'keyword', foreground: 'ff7b72', fontStyle: 'bold' },
          { token: 'identifier', foreground: 'e6edf3' },
          { token: 'number', foreground: '79c0ff' },
          { token: 'operator', foreground: 'd2a8ff' },
          { token: 'comment', foreground: '8b949e', fontStyle: 'italic' },
          { token: 'delimiter', foreground: 'c9d1d9' },
          { token: '@brackets', foreground: 'd2a8ff' },
        ],
        colors: {
          'editor.background': '#0d1117',
          'editor.foreground': '#e6edf3',
          'editorLineNumber.foreground': '#484f58',
          'editorLineNumber.activeForeground': '#c9d1d9',
          'editor.selectionBackground': '#264f78',
          'editor.lineHighlightBackground': '#161b22',
          'editorCursor.foreground': '#58a6ff',
          'editorWhitespace.foreground': '#21262d',
          'editorIndentGuide.background': '#21262d',
          'editorIndentGuide.activeBackground': '#30363d',
        },
      });
    }
  };

  const handleEditorDidMount = (editor: any, monaco: Monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    updateMarkers(editor, monaco, errors);
  };

  // Update error squigglies when errors change
  React.useEffect(() => {
    if (editorRef.current && monacoRef.current) {
      updateMarkers(editorRef.current, monacoRef.current, errors);
    }
  }, [errors]);

  const updateMarkers = (editor: any, monaco: Monaco, errList: CompilerError[]) => {
    const model = editor.getModel();
    if (!model) return;

    const markers = errList
      .filter((e) => e.line !== null && e.line !== undefined && e.line > 0)
      .map((e) => {
        const line = e.line!;
        const col = e.column && e.column > 0 ? e.column : 1;
        const lineContent = model.getLineContent(line) || '';
        return {
          startLineNumber: line,
          startColumn: col,
          endLineNumber: line,
          endColumn: Math.max(col + 1, lineContent.length + 1),
          message: `${e.error_type}: ${e.message}`,
          severity: monaco.MarkerSeverity.Error,
        };
      });

    monaco.editor.setModelMarkers(model, 'sudarshan', markers);
  };

  return (
    <div className="w-full h-full relative">
      <Editor
        height="100%"
        language="sudarshan"
        theme="sudarshan-dark"
        value={value}
        onChange={(val) => onChange(val || '')}
        beforeMount={handleEditorWillMount}
        onMount={handleEditorDidMount}
        options={{
          fontSize: 13,
          fontFamily: "'JetBrains Mono', monospace",
          fontLigatures: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          lineNumbers: 'on',
          renderLineHighlight: 'all',
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  );
};
