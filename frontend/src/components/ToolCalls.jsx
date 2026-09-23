import React, { useState } from 'react';

export default function ToolCalls({ toolCalls }) {
  const [expanded, setExpanded] = useState(true);
  if (!toolCalls || toolCalls.length === 0) return null;

  return (
    <div className="tool-calls-panel">
      <div className="tool-calls-header" onClick={() => setExpanded(!expanded)}>
        <div className="tool-calls-title">
          <div className="tool-calls-title-icon">⚙️</div>
          <span className="tool-calls-title-text">Tool Calls</span>
          <span className="tool-call-count">{toolCalls.length}</span>
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          {expanded ? '▲ Collapse' : '▼ Expand'}
        </span>
      </div>
      {expanded && (
        <div className="tool-calls-body">
          {toolCalls.map((tc, i) => (
            <div key={i} className="tool-call-item">
              <div className="tool-call-name">
                <span className="tool-call-name-badge">{tc.tool_name}</span>
                <span className={`tool-call-success ${tc.success ? 'success' : 'error'}`}>
                  {tc.success ? '✓ Success' : '✗ Failed'}
                </span>
              </div>
              <div className="tool-call-args">
                {JSON.stringify(tc.arguments, null, 2)}
              </div>
              <div className="tool-call-summary">{tc.result_summary}</div>
              {tc.error_message && (
                <div style={{ color: 'var(--accent-red)', fontSize: '0.82rem', marginTop: '6px' }}>
                  {tc.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
