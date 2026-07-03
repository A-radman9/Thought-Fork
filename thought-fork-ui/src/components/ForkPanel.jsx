/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import { useEffect, useRef } from 'react';
import MarkdownBlock from './MarkdownBlock';

export default function ForkPanel({ forkId, stance, text, tokens, duration, done, colorClass }) {
  const bodyRef = useRef(null);

  // Auto-scroll to bottom as text streams in
  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [text]);

  const isStreaming = text && !done;
  const durationSec = duration ? (duration / 1000).toFixed(1) : null;

  return (
    <div
      className={`fork-panel fork-panel--${colorClass} ${isStreaming ? 'fork-panel--streaming' : ''}`}
      id={`fork-panel-${forkId}`}
    >
      <div className="fork-panel__header">
        <div className="fork-panel__info">
          <span className="fork-panel__id">Fork {forkId}</span>
          <span className="fork-panel__badge">{stance}</span>
        </div>
        <div className="fork-panel__meta">
          {done && tokens > 0 && (
            <span className="fork-panel__token-badge">
              {tokens} tok · {durationSec}s
            </span>
          )}
          {isStreaming && (
            <span className="fork-panel__token-badge">streaming…</span>
          )}
        </div>
      </div>

      <div className="fork-panel__body" ref={bodyRef}>
        {text ? (
          <div className="fork-panel__text">
            <MarkdownBlock content={isStreaming ? text + ' ▍' : text} />
          </div>
        ) : (
          <div className="fork-panel__placeholder">
            Waiting for reasoning...
          </div>
        )}
      </div>
    </div>
  );
}
