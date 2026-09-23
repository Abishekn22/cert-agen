import React from 'react';

export default function ExecutionTime({ ms }) {
  if (ms === null || ms === undefined) return null;
  const seconds = (ms / 1000).toFixed(2);

  return (
    <div className="execution-time">
      <span className="execution-time-icon">⏱️</span>
      <span>{seconds}s ({ms}ms)</span>
    </div>
  );
}
