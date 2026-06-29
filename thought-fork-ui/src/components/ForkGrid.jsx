/* Copyright 2026 Ameen Saeed — Apache 2.0 License */

import ForkPanel from './ForkPanel';

export default function ForkGrid({ forks }) {
  const forkEntries = Object.entries(forks);

  if (forkEntries.length === 0) return null;

  return (
    <div className="fork-grid" id="fork-grid">
      {forkEntries.map(([id, fork]) => (
        <ForkPanel
          key={id}
          forkId={id}
          stance={fork.stance}
          text={fork.text}
          tokens={fork.tokens}
          duration={fork.duration}
          done={fork.done}
        />
      ))}
    </div>
  );
}
