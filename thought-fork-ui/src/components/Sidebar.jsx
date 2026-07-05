/* Copyright 2026 — Apache 2.0 License */

import React from 'react';

export default function Sidebar({ sessions, currentSessionId, onLoadSession, onNewSession }) {
  return (
    <div className="sidebar">
      <button className="sidebar__new-btn" onClick={onNewSession}>
        <span className="sidebar__new-icon">+</span>
        New Thought Fork
      </button>
      

      
      <div className="sidebar__list">
        <h3 className="sidebar__heading">Recent Sessions</h3>
        {sessions.length === 0 ? (
          <p className="sidebar__empty">No previous sessions.</p>
        ) : (
          sessions.map(s => (
            <button 
              key={s.id} 
              className={`sidebar__item ${s.id === currentSessionId ? 'sidebar__item--active' : ''}`}
              onClick={() => onLoadSession(s.id)}
            >
              {s.title}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
