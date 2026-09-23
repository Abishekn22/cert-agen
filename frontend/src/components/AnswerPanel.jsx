import React from 'react';

export default function AnswerPanel({ answer }) {
  if (!answer) return null;

  return (
    <div className="answer-panel">
      <div className="answer-header">
        <div className="answer-icon">🤖</div>
        <span className="answer-label">Agent Response</span>
      </div>
      <div className="answer-body">{answer}</div>
    </div>
  );
}
