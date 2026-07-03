/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import { useState, useCallback, useRef, useEffect } from 'react';

const API_BASE = 'http://localhost:8000';

export function useChatSession() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const sessionIdRef = useRef(null);
  
  // Historical turns in the current session
  const [turns, setTurns] = useState([]); 
  
  // Active streaming state
  const [state, setState] = useState('idle');
  const [activeSelectedStances, setActiveSelectedStances] = useState([]);
  const [activeForks, setActiveForks] = useState({});
  const [activeSynthesis, setActiveSynthesis] = useState({ text: '', tokens: 0, duration: 0, done: false });
  
  const abortRef = useRef(null);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/sessions`);
      if (res.ok) {
        const data = await res.json();
        setSessions(data);
      }
    } catch (e) {
      console.error('Failed to fetch sessions', e);
    }
  }, []);

  const loadSession = useCallback(async (id) => {
    if (abortRef.current) abortRef.current.abort();
    
    try {
      const res = await fetch(`${API_BASE}/sessions/${id}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentSessionId(data.session_id);
        sessionIdRef.current = data.session_id;
        setTurns(data.turns);
        
        // Reset active streaming state
        setState('idle');
        setActiveSelectedStances([]);
        setActiveForks({});
        setActiveSynthesis({ text: '', tokens: 0, duration: 0, done: false });
      }
    } catch (e) {
      console.error('Failed to load session', e);
    }
  }, []);

  const createNewSession = useCallback(() => {
    if (abortRef.current) abortRef.current.abort();
    setCurrentSessionId(null);
    sessionIdRef.current = null;
    setTurns([]);
    setState('idle');
    setActiveSelectedStances([]);
    setActiveForks({});
    setActiveSynthesis({ text: '', tokens: 0, duration: 0, done: false });
  }, []);

  const sendMessage = useCallback(async (prompt, forkCount = 3, options = {}) => {
    const { useDynamicStances = true, manualStances = [] } = options;

    setState('selecting');
    setActiveSelectedStances([]);
    setActiveForks({});
    setActiveSynthesis({ text: '', tokens: 0, duration: 0, done: false });

    const controller = new AbortController();
    abortRef.current = controller;

    const payload = {
      prompt,
      fork_count: forkCount,
      use_dynamic_stances: useDynamicStances,
      stances: manualStances.length > 0 ? manualStances : undefined,
    };
    
    if (sessionIdRef.current) {
      payload.session_id = sessionIdRef.current;
    }

    try {
      const response = await fetch(`${API_BASE}/fork`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

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
          if (jsonStr.startsWith('data: ')) {
            jsonStr = jsonStr.slice(6).trim();
          }

          try {
            const event = JSON.parse(jsonStr);
            processEvent(event);
          } catch (e) {
            // ignore JSON parse errors from partial chunks
          }
        }
      }
      
      // When done, reload session to put the active turn into history
      if (abortRef.current === controller) {
        // Wait briefly for db save
        setTimeout(() => {
          if (sessionIdRef.current) {
            loadSession(sessionIdRef.current);
            fetchSessions();
          }
        }, 500);
      }
      
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Fork stream error:', err);
        setState('idle');
      }
    }
  }, [currentSessionId, fetchSessions, loadSession]);

  function processEvent(event) {
    const { event_type, fork_id, stance, stances, chunk, token_count, duration_ms, session_id } = event;

    switch (event_type) {
      case 'stances_selected':
        setActiveSelectedStances(stances || []);
        setState('forking');
        break;

      case 'fork_start':
        setActiveForks(prev => ({
          ...prev,
          [fork_id]: { stance, text: '', tokens: 0, duration: 0, done: false }
        }));
        break;

      case 'fork_chunk':
        setActiveForks(prev => ({
          ...prev,
          [fork_id]: {
            ...prev[fork_id],
            text: (prev[fork_id]?.text || '') + (chunk || ''),
          }
        }));
        break;

      case 'fork_done':
        setActiveForks(prev => ({
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
        setActiveSynthesis(prev => ({
          ...prev,
          text: prev.text + (chunk || ''),
        }));
        break;

      case 'synthesis_done':
        setActiveSynthesis(prev => ({
          ...prev,
          tokens: token_count || 0,
          duration: duration_ms || 0,
          done: true,
        }));
        if (session_id && !sessionIdRef.current) {
          setCurrentSessionId(session_id);
          sessionIdRef.current = session_id;
          fetchSessions();
        }
        setState('complete');
        break;
    }
  }

  // Load sessions on mount
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  return {
    sessions,
    currentSessionId,
    turns,
    state,
    activeSelectedStances,
    activeForks,
    activeSynthesis,
    loadSession,
    createNewSession,
    sendMessage,
  };
}
