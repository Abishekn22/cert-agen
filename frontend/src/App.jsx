import React, { useState, useEffect, useCallback } from 'react';
import ChatInput from './components/ChatInput.jsx';
import AnswerPanel from './components/AnswerPanel.jsx';
import ToolCalls from './components/ToolCalls.jsx';
import ExecutionTime from './components/ExecutionTime.jsx';
import CertificateTable from './components/CertificateTable.jsx';
import LoadingState from './components/LoadingState.jsx';
import ErrorMessage from './components/ErrorMessage.jsx';
import { askAgent, checkHealth, createRenewal } from './services/api.js';

export default function App() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  // Confirmation state for action tools
  const [pendingAction, setPendingAction] = useState(null);
  const [confirmLoading, setConfirmLoading] = useState(false);

  // Health check on mount
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: 'degraded', ollama: 'unavailable', database: 'unknown' }));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!question.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setPendingAction(null);

    try {
      const res = await askAgent(question.trim());
      setResult(res);

      // Check if the response requires user confirmation (action tool)
      if (res.action_required) {
        setPendingAction(res.action_required);
      }
    } catch (err) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }, [question, loading]);

  const handleConfirm = useCallback(async () => {
    if (!pendingAction || confirmLoading) return;
    setConfirmLoading(true);
    setError(null);

    try {
      const renewalResult = await createRenewal(pendingAction.certificate_id, 'ops-agent');
      setPendingAction(null);
      setResult((prev) => ({
        ...prev,
        answer: `✅ Renewal request ${renewalResult.request_id} created successfully for certificate ${renewalResult.certificate_id}.`,
        action_required: null,
        records: [{
          certificate_id: renewalResult.certificate_id,
          customer_name: renewalResult.customer_name,
          status: renewalResult.status,
          domain: '—',
          expires_at: '—',
        }],
      }));
    } catch (err) {
      setError(err.message || 'Failed to create renewal request.');
    } finally {
      setConfirmLoading(false);
    }
  }, [pendingAction, confirmLoading]);

  const handleCancel = useCallback(() => {
    setPendingAction(null);
    setResult((prev) => prev ? { ...prev, answer: 'Renewal request was cancelled by the user.', action_required: null } : null);
  }, []);

  const handleClear = useCallback(() => {
    setQuestion('');
    setResult(null);
    setError(null);
    setPendingAction(null);
  }, []);

  const ollamaOnline = health?.ollama === 'available';
  const dbOnline = health?.database === 'available';

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="header-logo">🛡️</div>
          <div>
            <div className="header-title">CertAgen — AI Certificate Operations</div>
            <div className="header-subtitle">Enterprise Digital Certificate Lifecycle Agent</div>
          </div>
        </div>
        <div className="header-status">
          <div className="status-pill">
            <span className={`status-dot ${ollamaOnline ? 'online' : 'offline'}`} />
            Ollama {health?.model ? `(${health.model})` : ''}
          </div>
          <div className="status-pill">
            <span className={`status-dot ${dbOnline ? 'online' : 'offline'}`} />
            Database
          </div>
        </div>
      </header>

      {/* Chat Input */}
      <ChatInput
        question={question}
        setQuestion={setQuestion}
        onSubmit={handleSubmit}
        loading={loading}
        onClear={handleClear}
        hasResults={!!(result || error)}
      />

      {/* Loading */}
      {loading && <LoadingState />}

      {/* Error */}
      <ErrorMessage message={error} onDismiss={() => setError(null)} />

      {/* Confirmation Dialog */}
      {pendingAction && (
        <div className="confirmation-overlay">
          <div className="confirmation-header">
            <span className="confirmation-icon">⚠️</span>
            <span className="confirmation-title">Action Confirmation Required</span>
          </div>
          <div className="confirmation-body">
            <div>{pendingAction.description}</div>
            <div className="confirmation-details">
              <span className="confirmation-label">Action</span>
              <span className="confirmation-value">{pendingAction.action_type}</span>
              <span className="confirmation-label">Certificate</span>
              <span className="confirmation-value">{pendingAction.certificate_id}</span>
              {pendingAction.customer_name && (
                <>
                  <span className="confirmation-label">Customer</span>
                  <span className="confirmation-value">{pendingAction.customer_name}</span>
                </>
              )}
            </div>
          </div>
          <div className="confirmation-actions">
            <button className="btn btn-confirm" onClick={handleConfirm} disabled={confirmLoading}>
              {confirmLoading ? '⏳ Creating...' : '✓ Confirm Renewal'}
            </button>
            <button className="btn btn-cancel" onClick={handleCancel} disabled={confirmLoading}>
              ✕ Cancel
            </button>
          </div>
        </div>
      )}

      {/* Agent Response */}
      {result && !loading && (
        <>
          <AnswerPanel answer={result.answer} />
          <CertificateTable records={result.records} />
          <ToolCalls toolCalls={result.tool_calls} />
          <ExecutionTime ms={result.execution_time_ms} />
        </>
      )}
    </div>
  );
}
