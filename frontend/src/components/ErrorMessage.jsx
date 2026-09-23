import React from 'react';

export default function ErrorMessage({ message, onDismiss }) {
  if (!message) return null;

  return (
    <div className="error-container">
      <span className="error-icon">⚠️</span>
      <div style={{ flex: 1 }}>
        <div className="error-text">{message}</div>
      </div>
      {onDismiss && (
        <button
          className="btn btn-ghost"
          onClick={onDismiss}
          style={{ padding: '4px 10px', fontSize: '0.75rem' }}
        >
          Dismiss
        </button>
      )}
    </div>
  );
}
