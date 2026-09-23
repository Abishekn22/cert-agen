import React from 'react';

function getStatusClass(status) {
  if (!status) return '';
  const s = status.toUpperCase();
  if (s === 'ACTIVE') return 'active';
  if (s === 'EXPIRED') return 'expired';
  if (s === 'REVOKED') return 'revoked';
  if (s === 'PENDING') return 'pending';
  return '';
}

function getDaysClass(days) {
  if (days === undefined || days === null) return '';
  if (days <= 7) return 'critical';
  if (days <= 30) return 'warning';
  return 'safe';
}

export default function CertificateTable({ records }) {
  if (!records || records.length === 0) return null;

  // Determine which columns to show based on the data
  const hasRevocation = records.some(r => r.revoked !== undefined || r.revocation_date);
  const hasDaysRemaining = records.some(r => r.days_remaining !== undefined && r.days_remaining !== null);
  const hasCertType = records.some(r => r.certificate_type);

  return (
    <div className="cert-table-container">
      <div className="cert-table-header">
        <span style={{ fontSize: '14px' }}>📋</span>
        <span className="cert-table-title">Certificate Records</span>
        <span className="cert-table-count">{records.length} record{records.length > 1 ? 's' : ''}</span>
      </div>
      <div className="cert-table-scroll">
        <table className="cert-table">
          <thead>
            <tr>
              <th>Certificate ID</th>
              <th>Customer</th>
              <th>Domain</th>
              {hasCertType && <th>Type</th>}
              <th>Expires</th>
              {hasDaysRemaining && <th>Days Left</th>}
              <th>Status</th>
              {hasRevocation && <th>Revoked</th>}
              {hasRevocation && <th>Revocation Reason</th>}
            </tr>
          </thead>
          <tbody>
            {records.map((r, i) => (
              <tr key={i}>
                <td><span className="cert-id">{r.certificate_id}</span></td>
                <td>{r.customer_name}</td>
                <td><span className="cert-domain">{r.domain}</span></td>
                {hasCertType && <td>{r.certificate_type || '—'}</td>}
                <td>{r.expires_at || '—'}</td>
                {hasDaysRemaining && (
                  <td>
                    <span className={`days-remaining ${getDaysClass(r.days_remaining)}`}>
                      {r.days_remaining !== undefined && r.days_remaining !== null ? `${r.days_remaining}d` : '—'}
                    </span>
                  </td>
                )}
                <td>
                  <span className={`status-badge ${getStatusClass(r.status)}`}>
                    {r.status}
                  </span>
                </td>
                {hasRevocation && <td>{r.revoked ? '🔴 Yes' : '🟢 No'}</td>}
                {hasRevocation && <td>{r.revocation_reason || '—'}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
