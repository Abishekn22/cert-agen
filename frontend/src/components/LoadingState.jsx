import React from 'react';

export default function LoadingState() {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <div className="loading-text">
        Agent is processing your query<span className="loading-dots"></span>
      </div>
    </div>
  );
}
