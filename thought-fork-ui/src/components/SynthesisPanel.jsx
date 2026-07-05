/* Copyright 2026 — Apache 2.0 License */

import { useState, useEffect, useRef } from 'react';
import MarkdownBlock from './MarkdownBlock';

export default function SynthesisPanel({ text, tokens, duration, done, sessionId }) {
  const [copied, setCopied] = useState(false);
  const bodyRef = useRef(null);

  const isStreaming = text && !done;
  const durationSec = duration ? (duration / 1000).toFixed(1) : null;

  // Auto-scroll
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [text]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className={`synthesis ${isStreaming ? 'synthesis--streaming' : ''}`}
      id="synthesis-panel"
    >
      <div className="synthesis__header">
        <div className="synthesis__title">
          <span className="synthesis__title-icon">✦</span>
          Synthesis
          {isStreaming && <span style={{ fontWeight: 400, fontSize: '0.8rem', opacity: 0.6 }}>converging...</span>}
        </div>
        <div className="synthesis__actions">
          {done && (
            <button
              id="copy-synthesis-btn"
              className="synthesis__copy-btn"
              onClick={handleCopy}
            >
              {copied ? '✓ Copied' : '⎘ Copy'}
            </button>
          )}
        </div>
      </div>

      <div className="synthesis__body" ref={bodyRef}>
        <div className="synthesis__text">
          <MarkdownBlock content={isStreaming ? text + ' ▍' : text} />
        </div>
      </div>

      {done && (
        <div className="synthesis__meta">
          <span>{tokens} tokens · {durationSec}s</span>
          {sessionId && <span>Session: {sessionId}</span>}
        </div>
      )}
    </div>
  );
}
