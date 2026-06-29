/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import PromptInput from './components/PromptInput';
import ForkGrid from './components/ForkGrid';
import SynthesisPanel from './components/SynthesisPanel';
import { useForkStream } from './hooks/useForkStream';

const STATE_LABELS = {
  idle: null,
  forking: 'Forking — reasoning paths are streaming in parallel…',
  synthesizing: 'Converging — synthesizing all forks into a unified answer…',
  complete: null,
};

export default function App() {
  const { state, forks, synthesis, sessionId, startFork, reset } = useForkStream();

  const statusLabel = STATE_LABELS[state];
  const hasForks = Object.keys(forks).length > 0;
  const showSynthesis = state === 'synthesizing' || state === 'complete';

  // Compute totals for complete state
  const forkEntries = Object.values(forks);
  const totalForkTokens = forkEntries.reduce((sum, f) => sum + (f.tokens || 0), 0);
  const totalTokens = totalForkTokens + (synthesis.tokens || 0);

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__logo">
          <span className="header__icon">🔀</span>
          <h1 className="header__title">Thought Fork</h1>
        </div>
        <p className="header__subtitle">Branch your AI's reasoning like Git branches</p>
      </header>

      {/* Prompt Input */}
      <PromptInput onFork={startFork} onReset={reset} state={state} />

      {/* Status */}
      {statusLabel && (
        <div className="status" id="status-bar">
          <span className="status__dot" />
          <span>{statusLabel}</span>
        </div>
      )}

      {/* Fork Panels */}
      {hasForks && <ForkGrid forks={forks} />}

      {/* Synthesis */}
      {showSynthesis && (
        <SynthesisPanel
          text={synthesis.text}
          tokens={synthesis.tokens}
          duration={synthesis.duration}
          done={synthesis.done}
          sessionId={sessionId}
        />
      )}

      {/* Total summary when complete */}
      {state === 'complete' && (
        <div className="status" style={{ marginTop: '1rem', opacity: 0.6 }}>
          Total: {totalTokens} tokens across {forkEntries.length} forks + synthesis
        </div>
      )}
    </div>
  );
}
