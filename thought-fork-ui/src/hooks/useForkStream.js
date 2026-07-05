/* Copyright 2026 Thought Fork Contributors — Apache 2.0 License */

import { useState, useCallback, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

/**
 * Custom hook for streaming fork sessions via fetch + ReadableStream.
 *
 * State machine:
 *   idle → selecting → forking → synthesizing → complete
 *
 * 'selecting': AI is choosing the best reasoning perspectives for this prompt.
 * 'forking':   Parallel fork streams are streaming in.
 * 'synthesizing': All forks done, synthesis is streaming.
 * 'complete':  Everything done.
 */
export function useForkStream() {
  const [state, setState] = useState('idle');
  const [selectedStances, setSelectedStances] = useState([]); // [{id, name, description}]
  const [forks, setForks] = useState({});     // { A: { stance, text, tokens, duration, done } }
  const [synthesis, setSynthesis] = useState({ text: '', tokens: 0, duration: 0, done: false });
  const [sessionId, setSessionId] = useState(null);
  const abortRef = useRef(null);

  const startFork = useCallback(async (prompt, forkCount, useDynamicStances = true) => {
    // Reset all state
    setSelectedStances([]);
    setForks({});
    setSynthesis({ text: '', tokens: 0, duration: 0, done: false });
    setSessionId(null);
    setState('selecting'); // Phase 0: stance selection begins

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(`${API_BASE}/fork`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          fork_count: forkCount,
          use_dynamic_stances: useDynamicStances,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;

          let jsonStr = trimmed.slice(6).trim();
          if (!jsonStr) continue;

          // Handle double-prefixed data from SSE wrapping
          if (jsonStr.startsWith('data: ')) {
            jsonStr = jsonStr.slice(6).trim();
          }

          try {
            const event = JSON.parse(jsonStr);
            processEvent(event);
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Fork stream error:', err);
        setState('idle');
      }
    }
  }, []);

  function processEvent(event) {
    const { event_type, fork_id, stance, stances, chunk, token_count, duration_ms, session_id } = event;

    switch (event_type) {
      // Phase 0: Stance selection complete
      case 'stances_selected':
        setSelectedStances(stances || []);
        setState('forking');
        break;

      // Phase 1: Fork streaming
      case 'fork_start':
        setForks(prev => ({
          ...prev,
          [fork_id]: { stance, text: '', tokens: 0, duration: 0, done: false }
        }));
        break;

      case 'fork_chunk':
        setForks(prev => ({
          ...prev,
          [fork_id]: {
            ...prev[fork_id],
            text: (prev[fork_id]?.text || '') + (chunk || ''),
          }
        }));
        break;

      case 'fork_done':
        setForks(prev => ({
          ...prev,
          [fork_id]: {
            ...prev[fork_id],
            tokens: token_count || 0,
            duration: duration_ms || 0,
            done: true,
          }
        }));
        break;

      // Phase 2: Synthesis streaming
      case 'synthesis_chunk':
        setState('synthesizing');
        setSynthesis(prev => ({
          ...prev,
          text: prev.text + (chunk || ''),
        }));
        break;

      case 'synthesis_done':
        setSynthesis(prev => ({
          ...prev,
          tokens: token_count || 0,
          duration: duration_ms || 0,
          done: true,
        }));
        setSessionId(session_id);
        setState('complete');
        break;
    }
  }

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
    setState('idle');
    setSelectedStances([]);
    setForks({});
    setSynthesis({ text: '', tokens: 0, duration: 0, done: false });
    setSessionId(null);
  }, []);

  return {
    state,
    selectedStances,
    forks,
    synthesis,
    sessionId,
    startFork,
    reset,
  };
}
