/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import { useState, useCallback, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

/**
 * Custom hook for streaming fork sessions via fetch + ReadableStream.
 * We use fetch instead of EventSource because our endpoint is POST.
 */
export function useForkStream() {
  const [state, setState] = useState('idle'); // idle | forking | synthesizing | complete
  const [forks, setForks] = useState({});     // { A: { stance, text, tokens, duration, done } }
  const [synthesis, setSynthesis] = useState({ text: '', tokens: 0, duration: 0, done: false });
  const [sessionId, setSessionId] = useState(null);
  const abortRef = useRef(null);

  const startFork = useCallback(async (prompt, forkCount, stances) => {
    // Reset state
    setForks({});
    setSynthesis({ text: '', tokens: 0, duration: 0, done: false });
    setSessionId(null);
    setState('forking');

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const body = { prompt, fork_count: forkCount };
      if (stances && stances.length > 0) {
        body.stances = stances;
      }

      const response = await fetch(`${API_BASE}/fork`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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

        // Process complete SSE lines
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data: ')) continue;

          const jsonStr = trimmed.slice(6).trim();
          if (!jsonStr || jsonStr === '') continue;

          // Handle potential double-prefixed data from SSE wrapping
          let cleanJson = jsonStr;
          if (cleanJson.startsWith('data: ')) {
            cleanJson = cleanJson.slice(6).trim();
          }

          try {
            const event = JSON.parse(cleanJson);
            processEvent(event);
          } catch {
            // skip malformed JSON
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Fork stream error:', err);
      }
    }
  }, []);

  function processEvent(event) {
    const { event_type, fork_id, stance, chunk, is_done, token_count, duration_ms, session_id } = event;

    switch (event_type) {
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
    setForks({});
    setSynthesis({ text: '', tokens: 0, duration: 0, done: false });
    setSessionId(null);
  }, []);

  return {
    state,
    forks,
    synthesis,
    sessionId,
    startFork,
    reset,
  };
}
