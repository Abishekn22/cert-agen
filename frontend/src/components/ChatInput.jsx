import React from 'react';

const EXAMPLE_QUERIES = [
  'Show certificates expiring in the next 30 days',
  'Show certificates expiring next month',
  'Check certificate ABC123 status',
  'Is certificate XYZ789 revoked?',
  'Generate renewal request for ABC123',
  'List certificates belonging to Customer A',
];

export default function ChatInput({ question, setQuestion, onSubmit, loading, onClear, hasResults }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    if (question.trim() && !loading) onSubmit();
  };

  return (
    <div>
      <div className="quick-actions">
        {EXAMPLE_QUERIES.map((q, i) => (
          <button
            key={i}
            className="quick-chip"
            onClick={() => { setQuestion(q); }}
            disabled={loading}
          >
            {q}
          </button>
        ))}
      </div>
      <form className="chat-input-container" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder="Ask the operations agent a question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
          {loading ? '⏳ Processing...' : '🔍 Ask Agent'}
        </button>
        {hasResults && (
          <button type="button" className="btn btn-ghost" onClick={onClear} disabled={loading}>
            ✕ Clear
          </button>
        )}
      </form>
    </div>
  );
}
