import React, { useState } from 'react';

export default function IncidentsView({
  incidents,
  selectedIncident,
  onSelectIncident,
  onCloseModal,
  onDetectAndInvestigate,
  onApproveRemediation,
  onExecuteRemediation,
  isInvestigating,
  isExecuting,
  isApproving
}) {
  const [approverName, setApproverName] = useState('Incident-Commander-Alice');
  const [simulateFail, setSimulateFail] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'AWAITING_APPROVAL':
        return <span className="badge badge-awaiting"><span className="badge-dot" /> Awaiting Approval</span>;
      case 'APPROVED':
        return <span className="badge badge-approved"><span className="badge-dot" /> Approved</span>;
      case 'REMEDIATING':
      case 'VERIFYING':
        return <span className="badge badge-remediating"><span className="badge-dot" /> {status}</span>;
      case 'RESOLVED':
        return <span className="badge badge-resolved"><span className="badge-dot" /> Resolved</span>;
      case 'RETRYING':
        return <span className="badge badge-retrying"><span className="badge-dot" /> Retrying</span>;
      case 'FAILED_ESCALATED':
      case 'REJECTED':
        return <span className="badge badge-escalated"><span className="badge-dot" /> {status}</span>;
      default:
        return <span className="badge badge-awaiting">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Action Header */}
      <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Active Production Incidents & Resolution Flow</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>
            Closed-loop incident life cycle with strict human-in-the-loop approval gate and post-remediation SLO verification.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={onDetectAndInvestigate}
          disabled={isInvestigating}
        >
          {isInvestigating ? 'Analyzing Telemetry & Running RCA...' : '⚡ Detect Anomaly & Run RCA'}
        </button>
      </div>

      {/* Incidents Table */}
      <div className="glass-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        {incidents.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--text-muted)' }}>
            <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🛡️</div>
            <h4>No Active or Archived Incidents Yet</h4>
            <p style={{ fontSize: '0.86rem', marginTop: '4px' }}>
              Trigger a controlled fault in the Fault Simulator tab, then click "Detect Anomaly & Run RCA".
            </p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Incident ID</th>
                <th>Target</th>
                <th>Title / Scope</th>
                <th>Culprit Service</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Retries</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => (
                <tr key={inc.id} style={{ background: inc.is_active ? 'rgba(239, 68, 68, 0.05)' : undefined }}>
                  <td>
                    <code>{inc.id}</code>
                    <div style={{ marginTop: '2px' }}>
                      {inc.is_active ? (
                        <span className="badge badge-escalated" style={{ fontSize: '0.68rem', padding: '1px 6px', fontWeight: 700 }}>🔴 LIVE ACTIVE</span>
                      ) : (
                        <span className="badge badge-simulation" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>📁 Archived</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className="badge" style={{ fontSize: '0.74rem', background: inc.target_system === 'shopease' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(99, 102, 241, 0.1)', color: inc.target_system === 'shopease' ? '#059669' : '#4f46e5' }}>
                      {inc.target_system === 'shopease' ? '🛒 ShopEase' : '🧪 Simulator'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, maxWidth: '280px' }}>{inc.title}</td>
                  <td><span style={{ color: 'var(--accent-cyan)' }}>{inc.culprit_service}</span></td>
                  <td>{renderStatusBadge(inc.status)}</td>
                  <td>
                    <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>
                      {(inc.confidence_score * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <span style={{ color: inc.retry_count > 0 ? 'var(--accent-amber)' : 'var(--text-muted)' }}>
                      {inc.retry_count} / {inc.max_retries}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-dim)', fontSize: '0.8rem' }}>
                    {inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : ''}
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => onSelectIncident(inc.id)}
                    >
                      Inspect RCA & Fix
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Incident Detail & Closed-Loop Console Modal */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={onCloseModal}>
          <div className="modal-card glass-panel" onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '16px' }}>
              <div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '6px' }}>
                  <code style={{ fontSize: '0.95rem', color: 'var(--accent-cyan)' }}>{selectedIncident.id}</code>
                  {renderStatusBadge(selectedIncident.status)}
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                    Retries: {selectedIncident.retry_count}/{selectedIncident.max_retries}
                  </span>
                </div>
                <h3 style={{ fontSize: '1.25rem' }}>{selectedIncident.title}</h3>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Culprit Service: <strong style={{ color: '#fff' }}>{selectedIncident.culprit_service}</strong> | Severity: <strong>{selectedIncident.severity}</strong>
                </div>
              </div>
              <button
                className="btn btn-secondary btn-sm"
                onClick={onCloseModal}
              >
                ✕ Close
              </button>
            </div>

            {/* Evidence & Symptoms */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '16px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-amber)', marginBottom: '8px' }}>⚡ Anomaly Symptoms</h4>
                <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: 1.5 }}>{selectedIncident.symptoms}</p>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '0.9rem', color: 'var(--accent-emerald)', marginBottom: '8px' }}>
                  🧠 AI Root Cause Diagnosis ({((selectedIncident.confidence_score || 0) * 100).toFixed(0)}% Confidence)
                </h4>
                <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: 1.5 }}>{selectedIncident.rca_summary}</p>
              </div>

              {/* Evidence Signals List */}
              {selectedIncident.evidence && selectedIncident.evidence.length > 0 && (
                <div style={{ gridColumn: '1 / -1', background: 'rgba(0,0,0,0.25)', padding: '14px', borderRadius: '8px' }}>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginBottom: '8px' }}>
                    🔍 Corroborating Telemetry & Log Evidence ({selectedIncident.evidence.length} Signals)
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '8px' }}>
                    {selectedIncident.evidence.map((ev, idx) => (
                      <div key={idx} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                          <span style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>{ev.type?.toUpperCase()}</span>
                          {ev.value && <code style={{ color: 'var(--accent-rose)' }}>{ev.value}</code>}
                        </div>
                        <div style={{ color: '#cbd5e1' }}>{ev.detail || ev.message || JSON.stringify(ev)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Retrieved Historical Precedents */}
            {selectedIncident.retrieved_cases && selectedIncident.retrieved_cases.length > 0 && (
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '16px', borderRadius: '8px' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '10px', color: 'var(--accent-indigo)' }}>
                  📚 Retrieved Historical Precedents (Adaptive Matching)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedIncident.retrieved_cases.map((c) => (
                    <div key={c.id} style={{ background: 'rgba(255,255,255,0.03)', padding: '10px 14px', borderRadius: '6px', fontSize: '0.84rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                        <strong>{c.id}: {c.title}</strong>
                        <span style={{ color: 'var(--accent-cyan)' }}>Sim: {(c.similarity_score * 100).toFixed(1)}%</span>
                      </div>
                      <div style={{ color: 'var(--text-muted)' }}>{c.root_cause}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Proposed Safe Allowlisted Remediation */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(6, 182, 212, 0.08))',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              padding: '20px',
              borderRadius: '10px'
            }}>
              <h4 style={{ fontSize: '1rem', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                🛡️ Safe Allowlisted Remediation Action
              </h4>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', marginBottom: '12px', fontSize: '0.88rem' }}>
                <div>Action: <code style={{ color: 'var(--accent-cyan)' }}>{selectedIncident.proposed_action}</code></div>
                <div>Risk Level: <strong style={{ color: selectedIncident.risk_level === 'LOW' ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>{selectedIncident.risk_level}</strong></div>
                <div>Reversible: <span style={{ color: 'var(--accent-emerald)' }}>✓ Guaranteed</span></div>
              </div>

              {/* Approval Gate Form */}
              {selectedIncident.status === 'AWAITING_APPROVAL' && (
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', marginTop: '12px' }}>
                  <h5 style={{ fontSize: '0.88rem', marginBottom: '10px', color: 'var(--accent-amber)' }}>
                    Human-in-the-Loop Explicit Approval Required
                  </h5>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <input
                      type="text"
                      placeholder="Approver Name / Role"
                      value={approverName}
                      onChange={(e) => setApproverName(e.target.value)}
                      style={{ flex: 1, minWidth: '220px' }}
                    />
                    <button
                      className="btn btn-success"
                      onClick={() => onApproveRemediation(selectedIncident.id, true, approverName)}
                      disabled={isApproving}
                    >
                      {isApproving ? 'Approving...' : '✓ Approve Safe Fix'}
                    </button>
                    <button
                      className="btn btn-danger"
                      onClick={() => onApproveRemediation(selectedIncident.id, false, approverName, rejectionReason)}
                      disabled={isApproving}
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>
              )}

              {/* Execution & Verification Trigger */}
              {(selectedIncident.status === 'APPROVED' || selectedIncident.status === 'RETRYING') && (
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '16px', borderRadius: '8px', marginTop: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                        Ready for Safe Automated Execution
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                        Approved by: {selectedIncident.approved_by}
                      </div>
                    </div>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', cursor: 'pointer', color: 'var(--text-muted)' }}>
                      <input
                        type="checkbox"
                        checked={simulateFail}
                        onChange={(e) => setSimulateFail(e.target.checked)}
                      />
                      🧪 Simulate Verification Failure (Test Safe Retry Loop)
                    </label>
                  </div>

                  <button
                    className="btn btn-primary"
                    style={{ width: '100%' }}
                    onClick={() => onExecuteRemediation(selectedIncident.id, simulateFail)}
                    disabled={isExecuting}
                  >
                    {isExecuting ? 'Executing Allowlisted Fix & Verifying SLOs...' : '⚡ Execute Allowlisted Remediation & Verify Recovery'}
                  </button>
                </div>
              )}

              {/* Verification & Resolution Result Display */}
              {selectedIncident.verification_details && selectedIncident.verification_details.status && (
                <div style={{
                  background: selectedIncident.verification_details.status === 'PASSED' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                  border: `1px solid ${selectedIncident.verification_details.status === 'PASSED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
                  padding: '16px',
                  borderRadius: '8px',
                  marginTop: '16px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <strong style={{ color: selectedIncident.verification_details.status === 'PASSED' ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                      SLO Verification Result: {selectedIncident.verification_details.status}
                    </strong>
                    {renderStatusBadge(selectedIncident.status)}
                  </div>

                  <p style={{ fontSize: '0.85rem', marginBottom: '10px' }}>{selectedIncident.verification_details.details}</p>

                  {selectedIncident.verification_details.slo_checks && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '0.78rem' }}>
                      {Object.entries(selectedIncident.verification_details.slo_checks).map(([check, passed]) => (
                        <span key={check} className="badge" style={{
                          background: passed ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
                          color: passed ? '#6ee7b7' : '#fda4af',
                          borderColor: passed ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'
                        }}>
                          {passed ? '✓' : '✕'} {check.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  )}

                  {selectedIncident.resolution_summary && (
                    <div style={{ marginTop: '12px', fontSize: '0.85rem', color: '#e2e8f0' }}>
                      <strong>Resolution Summary:</strong> {selectedIncident.resolution_summary}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
