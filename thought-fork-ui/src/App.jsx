/* Copyright 2026 Thought Fork Contributors — Apache 2.0 License */

import React, { useState } from 'react';
import PromptInput from './components/PromptInput';
import Sidebar from './components/Sidebar';
import ChatFeed from './components/ChatFeed';
import { useChatSession } from './hooks/useChatSession';

export default function App() {
  const { 
    sessions, 
    currentSessionId, 
    turns, 
    state, 
    activeSelectedStances, 
    activeForks, 
    activeSynthesis, 
    loadSession, 
    createNewSession, 
    sendMessage 
  } = useChatSession();

  const [activePrompt, setActivePrompt] = useState("");

  const handleSendMessage = (prompt, forkCount, options) => {
    setActivePrompt(prompt);
    sendMessage(prompt, forkCount, options);
  };

  return (
    <div className="app-container">
      <Sidebar 
        sessions={sessions} 
        currentSessionId={currentSessionId}
        onLoadSession={loadSession}
        onNewSession={createNewSession}
      />
      
      <main className="main-chat">
        {turns.length === 0 && state === 'idle' && (
          <header className="header">
            <div className="header__logo">
              <span className="header__icon">🔀</span>
              <h1 className="header__title">Thought Fork</h1>
            </div>
            <p className="header__subtitle">Explore AI reasoning in parallel</p>
          </header>
        )}
        
        <ChatFeed 
          turns={turns}
          state={state}
          activePrompt={activePrompt}
          activeSelectedStances={activeSelectedStances}
          activeForks={activeForks}
          activeSynthesis={activeSynthesis}
        />
        
        <div className="input-area">
          <PromptInput 
            onSend={handleSendMessage} 
            state={state} 
          />
        </div>
      </main>
    </div>
  );
}
