/* Copyright 2026 — Apache 2.0 License */

import React, { useEffect, useRef } from 'react';
import MarkdownBlock from './MarkdownBlock';
import StancePreview from './StancePreview';
import ForkGrid from './ForkGrid';
import SynthesisPanel from './SynthesisPanel';

function TurnMessage({ turn }) {
  return (
    <div className="chat-turn">
      <div className="chat-message user-message">
        <div className="message-content">{turn.prompt}</div>
      </div>
      <div className="chat-message ai-message">
        <div className="ai-message-inner">
          {turn.forks && turn.forks.length > 0 && (
            <details className="ai-reasoning">
              <summary>View AI Reasoning ({turn.forks.length} forks)</summary>
              <div className="ai-reasoning-content">
                <ForkGrid forks={Object.fromEntries((turn.forks || []).map(f => [f.fork_id, {
                  stance: f.stance,
                  text: f.output,
                  tokens: f.token_count,
                  duration: f.duration_ms,
                  done: true,
                }]))} />
              </div>
            </details>
          )}
          <div className="synthesis-content">
            <MarkdownBlock content={turn.synthesis || "*Synthesis failed or was incomplete.*"} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatFeed({ 
  turns, 
  state, 
  activePrompt,
  activeSelectedStances, 
  activeForks, 
  activeSynthesis
}) {
  const feedRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [turns, state, activeForks, activeSynthesis]);

  const hasForks = Object.keys(activeForks).length > 0;
  const showStancePreview = state === 'selecting' || (state === 'forking' && !hasForks);

  return (
    <div className="chat-feed" ref={feedRef}>
      {turns.map(turn => (
        <TurnMessage key={turn.turn_id} turn={turn} />
      ))}
      
      {/* Active turn streaming */}
      {state !== 'idle' && (
        <div className="chat-turn">
          <div className="chat-message user-message">
            <div className="message-content">{activePrompt}</div>
          </div>
          <div className="chat-message ai-message">
            <div className="ai-message-inner">
              {showStancePreview && (
                <StancePreview stances={activeSelectedStances} />
              )}
              
              {hasForks && (
                <details className="ai-reasoning" open={state === 'forking'}>
                  <summary>View AI Reasoning ({Object.keys(activeForks).length} forks)</summary>
                  <div className="ai-reasoning-content">
                    <ForkGrid forks={activeForks} />
                  </div>
                </details>
              )}
              
              {(state === 'synthesizing' || state === 'complete' || activeSynthesis.text) && (
                <SynthesisPanel
                  text={activeSynthesis.text}
                  tokens={activeSynthesis.tokens}
                  duration={activeSynthesis.duration}
                  done={activeSynthesis.done}
                />
              )}
            </div>
          </div>
        </div>
      )}
      <div className="chat-spacer" />
    </div>
  );
}
