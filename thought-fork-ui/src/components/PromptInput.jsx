/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import { useState } from 'react';

export default function PromptInput({ onFork, onReset, state }) {
  const [prompt, setPrompt] = useState('');
  const [forkCount, setForkCount] = useState(3);

  const isRunning = state === 'selecting' || state === 'forking' || state === 'synthesizing';
  const isComplete = state === 'complete';

  const handleFork = () => {
    if (!prompt.trim() || isRunning) return;
    // Always use dynamic stances — the AI will choose the best ones
    onFork(prompt.trim(), forkCount, true);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      handleFork();
    }
  };

  const handleReset = () => {
    setPrompt('');
    onReset();
  };

  return (
    <div className="prompt">
      <div className="prompt__box">
        <textarea
          id="prompt-input"
          className="prompt__textarea"
          placeholder="Ask anything. Thought Fork will select the best reasoning perspectives for your question…"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={isRunning}
        />

        <div className="prompt__actions">
          <div className="prompt__config">
            <span className="prompt__label">Forks:</span>
            <select
              id="fork-count-select"
              className="prompt__select"
              value={forkCount}
              onChange={(e) => setForkCount(Number(e.target.value))}
              disabled={isRunning}
            >
              {[2, 3, 4, 5].map(n => (
                <option key={n} value={n}>{n} paths</option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            {isComplete && (
              <button
                id="reset-btn"
                className="prompt__btn prompt__btn--reset"
                onClick={handleReset}
              >
                ↻ New Fork
              </button>
            )}
            <button
              id="fork-btn"
              className="prompt__btn"
              onClick={handleFork}
              disabled={!prompt.trim() || isRunning}
            >
              {state === 'selecting' ? (
                <>🧠 Selecting…</>
              ) : state === 'forking' || state === 'synthesizing' ? (
                <>⏳ Forking…</>
              ) : (
                <>🔀 Fork</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
