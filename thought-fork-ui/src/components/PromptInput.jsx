/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import { useState, useRef } from 'react';

export default function PromptInput({ onSend, state }) {
  const [prompt, setPrompt] = useState('');
  const [forkCount, setForkCount] = useState('auto');
  const [manualStancesInput, setManualStancesInput] = useState('');

  const isRunning = state === 'selecting' || state === 'forking' || state === 'synthesizing';

  const textareaRef = useRef(null);

  const handleInput = (e) => {
    setPrompt(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const handleSend = () => {
    if (!prompt.trim() || isRunning) return;
    const currentPrompt = prompt.trim();
    
    const manualStances = manualStancesInput.split(',').map(s => s.trim()).filter(s => s.length > 0);
    
    setPrompt(''); // Clear input for chat feel
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
    onSend(currentPrompt, forkCount, { manualStances });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey || !e.shiftKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="prompt">
      <div className="prompt__box">
        <textarea
          id="prompt-input"
          ref={textareaRef}
          className="prompt__textarea"
          placeholder="Ask anything. Thought Fork will reason through parallel paths..."
          value={prompt}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={isRunning}
        />

        <div className="prompt__actions">
          <div className="prompt__config">
            <span className="prompt__label">Forks:</span>
            <select
              id="fork-count-input"
              className="prompt__select"
              value={forkCount}
              onChange={(e) => setForkCount(e.target.value === 'auto' ? 'auto' : parseInt(e.target.value))}
              disabled={isRunning}
              style={{ width: '5rem', textAlign: 'center' }}
            >
              <option value="auto">Auto</option>
              <option value="2">2</option>
              <option value="3">3</option>
              <option value="4">4</option>
              <option value="5">5</option>
              <option value="6">6</option>
              <option value="7">7</option>
            </select>
          </div>

          <div className="prompt__config" style={{ marginLeft: '1rem', flex: 1 }}>
            <span className="prompt__label">Stances:</span>
            <input
              type="text"
              className="prompt__select"
              placeholder="e.g. Lawyer, Skeptic (Optional)"
              value={manualStancesInput}
              onChange={(e) => setManualStancesInput(e.target.value)}
              disabled={isRunning}
              style={{ flex: 1 }}
            />
          </div>

          <button
            id="fork-btn"
            className="prompt__btn"
            onClick={handleSend}
            disabled={!prompt.trim() || isRunning}
          >
            {state === 'selecting' ? '🧠' : 
             state === 'forking' || state === 'synthesizing' ? '⏳' : 
             '🔀 Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
