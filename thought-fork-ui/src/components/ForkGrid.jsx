/* Copyright 2026 Thought Fork Contributors — Apache 2.0 License */

import ForkPanel from './ForkPanel';

// Color palette cycled by fork index — guarantees every fork gets a distinct color
// regardless of its AI-generated stance name.
const FORK_COLORS = [
  'blue',    // Fork A
  'amber',   // Fork B
  'rose',    // Fork C
  'green',   // Fork D
  'purple',  // Fork E
  'cyan',    // Fork F
  'gray',    // Fork G
];

export default function ForkGrid({ forks }) {
  const forkEntries = Object.entries(forks);

  if (forkEntries.length === 0) return null;

  return (
    <div className="fork-grid" id="fork-grid">
      {forkEntries.map(([id, fork], index) => (
        <ForkPanel
          key={id}
          forkId={id}
          stance={fork.stance}
          text={fork.text}
          tokens={fork.tokens}
          duration={fork.duration}
          done={fork.done}
          colorClass={FORK_COLORS[index % FORK_COLORS.length]}
        />
      ))}
    </div>
  );
}
