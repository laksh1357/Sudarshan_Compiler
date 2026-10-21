import React, { useRef, useEffect, useState } from 'react';

interface SourceEditorProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
}

export const SourceEditor: React.FC<SourceEditorProps> = ({
  value,
  onChange,
  onClear,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  // Compute line count
  const lines = value.split('\n');
  const lineCount = Math.max(lines.length, 1);

  // Sync scrolling between textarea and line numbers
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Support Tab key to insert 4 spaces
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newValue = value.substring(0, start) + '    ' + value.substring(end);
      onChange(newValue);

      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 4;
      }, 0);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <section className="pane editor-pane">
      <div className="pane-header">
        <div className="pane-title">
          <span className="pane-icon">📝</span>
          <h2>Sudarshan Source Code</h2>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={onClear}
            className="btn-sm btn-ghost"
            title="Clear Editor"
          >
            Clear
          </button>
          <button
            onClick={handleCopy}
            className="btn-sm btn-ghost"
            title="Copy Code"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="editor-container">
        {/* Line Numbers */}
        <div ref={lineNumbersRef} className="line-numbers">
          {Array.from({ length: lineCount }, (_, i) => (
            <div key={i + 1}>{i + 1}</div>
          ))}
        </div>

        {/* Text Area */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
          className="code-editor"
          spellCheck={false}
          placeholder={`// Type your Sudarshan code here...\n\nint a = 15;\nint b = a + 25;\nprint(b);`}
        />
      </div>
    </section>
  );
};
