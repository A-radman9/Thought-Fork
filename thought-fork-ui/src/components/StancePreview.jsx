/* Copyright 2026 — Apache 2.0 License */

import { useEffect, useState } from 'react';

/**
 * StancePreview — shown during the 'selecting' phase.
 *
 * Displays the AI-selected stances as animated cards that appear
 * one by one as if being revealed, creating a sense of the AI
 * "thinking about" which perspectives to use.
 */
export default function StancePreview({ stances }) {
  // Track which card indexes have been revealed (for staggered animation)
  const [revealed, setRevealed] = useState(new Set());

  useEffect(() => {
    if (!stances || stances.length === 0) return;

    // Reveal cards one by one with a stagger
    stances.forEach((_, i) => {
      setTimeout(() => {
        setRevealed(prev => new Set([...prev, i]));
      }, i * 180); // 180ms stagger between each card
    });
  }, [stances]);

  // Reset revealed state when stances change
  useEffect(() => {
    setRevealed(new Set());
  }, [stances?.length]);

  return (
    <div className="stance-preview" id="stance-preview">
      <div className="stance-preview__title">
        <span className="stance-preview__title-dot" />
        Selecting reasoning perspectives
      </div>
      <div className="stance-preview__cards">
        {stances.map((stance, i) => (
          <div
            key={stance.id}
            className={`stance-card ${revealed.has(i) ? 'stance-card--revealed' : ''}`}
            id={`stance-card-${stance.id}`}
          >
            <span className="stance-card__id">Fork {stance.id}</span>
            <div className="stance-card__content">
              <div className="stance-card__name">
                {stance.name.replace(/-/g, ' ')}
              </div>
              {stance.description && (
                <div className="stance-card__desc">{stance.description}</div>
              )}
            </div>
          </div>
        ))}

        {/* Placeholder skeletons while selection is still happening */}
        {stances.length === 0 && [0, 1, 2].map(i => (
          <div key={i} className="stance-card stance-card--revealed" style={{ opacity: 0.3 }}>
            <span className="stance-card__id">···</span>
            <div className="stance-card__content">
              <div className="stance-card__name" style={{ background: 'var(--border-subtle)', height: '14px', borderRadius: '4px', width: '120px' }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
