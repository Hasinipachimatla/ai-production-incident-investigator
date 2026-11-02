import React, { useState, useEffect } from 'react';

export default function GuidedInvestigation({
  catalog,
  activeFaults,
  telemetry,
  incidents,
  selectedIncident,
  onSelectIncident,
  onTriggerFault,
  onResetFault,
  onResetAllFaults,
  onDetectAndInvestigate,
  onApproveRemediation,
  onExecuteRemediation,
  isInvestigating,
  isExecuting,
  isApproving,
  isResetting,
  targetEnvironment = 'shopease',
  shopeaseHealth,
  workloadStatus = null,
  onToggleWorkload = null
}) {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedScenarioIndex, setSelectedScenarioIndex] = useState(0);
  const [approverName, setApproverName] = useState('Incident-Commander-Alice');
  const [simulateFail, setSimulateFail] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const isShopEase = targetEnvironment === 'shopease';
  const isConnected = isShopEase ? Boolean(shopeaseHealth?.connected) : true;
  const selectedScenario = catalog[selectedScenarioIndex] || catalog[0] || null;
  const isSelectedFaultActive = selectedScenario && activeFaults.includes(selectedScenario.fault_type);
  const hasActiveFaults = activeFaults.length > 0;

  // Auto-progress stepper based on real backend lifecycle state
  useEffect(() => {
    if (selectedIncident) {
      if (selectedIncident.status === 'RESOLVED') {
        setCurrentStep(7);
      } else if (selectedIncident.status === 'RETRYING' || selectedIncident.status === 'FAILED_ESCALATED') {
        setCurrentStep(7);
      } else if (selectedIncident.status === 'APPROVED') {
        setCurrentStep(7);
      } else if (selectedIncident.status === 'AWAITING_APPROVAL') {
        setCurrentStep(6);
      } else {
        setCurrentStep(4);
      }
    } else if (hasActiveFaults) {
      setCurrentStep(3);
    } else {
      setCurrentStep(1);
    }
  }, [selectedIncident, hasActiveFaults]);

  const handleTriggerCurrentScenario = async () => {
    if (!selectedScenario) return;
    await onTriggerFault(selectedScenario.fault_type);
    setCurrentStep(3);
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'AWAITING_APPROVAL':
        return <span className="badge badge-awaiting"><span className="badge-dot" /> Awaiting Human Approval</span>;
      case 'APPROVED':
        return <span className="badge badge-approved"><span className="badge-dot" /> Approved by Operator</span>;
      case 'REMEDIATING':
      case 'VERIFYING':
        return <span className="badge badge-remediating"><span className="badge-dot" /> {status}</span>;
      case 'RESOLVED':
        return <span className="badge badge-resolved"><span className="badge-dot" /> Resolved & Closed</span>;
      case 'RETRYING':
        return <span className="badge badge-retrying"><span className="badge-dot" /> Retrying ({selectedIncident?.retry_count || 1}/{selectedIncident?.max_retries || 3})</span>;
      case 'FAILED_ESCALATED':
        return <span className="badge badge-escalated"><span className="badge-dot" /> Escalated to Human On-Call</span>;
      case 'REJECTED':
        return <span className="badge badge-escalated"><span className="badge-dot" /> Rejected</span>;
      default:
        return <span className="badge badge-awaiting">{status}</span>;
    }
  };

  const logs = telemetry?.logs || [];
  const metrics = telemetry?.metrics || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px', animation: 'fadeIn 0.2s ease' }}>
      {/* Stepper Progress Card */}
      <div className="glass-panel" style={{ padding: '20px 26px', background: '#ffffff' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)' }}>
              Step-by-Step Incident Investigation & Recovery Workflow
            </h3>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>
              Follow the guided sequence from controlled failure injection to verified recovery
            </p>
          </div>
          {hasActiveFaults && (
            <button
              className="btn btn-danger btn-sm"
              onClick={onResetAllFaults}
              disabled={isResetting}
            >
              {isResetting ? 'Clearing...' : `Clear Active Faults (${activeFaults.length})`}
            </button>
          )}
        </div>

        {/* Stepper Bar */}
        <div className="stepper-container">
          {[
            { num: 1, title: '1. Select Fault' },
            { num: 2, title: '2. Inject Fault' },
            { num: 3, title: '3. Scan Telemetry' },
            { num: 4, title: '4. AI Root Cause' },
            { num: 5, title: '5. History Match' },
            { num: 6, title: '6. Human Gate' },
            { num: 7, title: '7. Verify & Close' }
          ].map((s) => {
            const isCompleted = currentStep > s.num || (s.num === 7 && selectedIncident?.status === 'RESOLVED');
            const isActive = currentStep === s.num;
            return (
              <div
                key={s.num}
                className={`step-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}`}
                onClick={() => setCurrentStep(s.num)}
              >
                <div className="step-bubble">
                  {isCompleted ? '✓' : s.num}
                </div>
                <span className="step-title">{s.title}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Interactive Stage Box */}
      <div className="glass-panel" style={{ padding: '26px 30px', background: '#ffffff' }}>
        {/* STEP 1 & 2: SELECT & TRIGGER FAULT */}
        {(currentStep === 1 || currentStep === 2) && (
          <div>
            <div style={{ marginBottom: '18px' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px', flexWrap: 'wrap' }}>
                <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)' }}>
                  Step {currentStep} of 7: Controlled Fault Scenario Selection
                </span>
                <span className="badge" style={{ background: isShopEase ? 'rgba(16, 185, 129, 0.1)' : 'rgba(99, 102, 241, 0.1)', color: isShopEase ? '#059669' : '#4f46e5' }}>
                  Target: {isShopEase ? '🛒 Live ShopEase (:5000)' : '🧪 Internal Simulator'}
                </span>
              </div>
              <h4 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                Choose a Microservice Failure Scenario
              </h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                {isShopEase
                  ? 'Select one of the 5 controlled scenarios to inject real telemetry perturbation into the live ShopEase application.'
                  : 'Select one of the 5 controlled scenarios to inject simulated telemetry into the internal testbed.'}
              </p>
            </div>

            {isShopEase && !isConnected && (
              <div style={{
                marginBottom: '18px',
                padding: '12px 16px',
                background: '#fffbeb',
                border: '1px solid #fde68a',
                borderRadius: '8px',
                color: '#92400e',
                fontSize: '0.88rem'
              }}>
                ⚠️ <strong>ShopEase is currently offline on port 5000.</strong> Start it with <code>npm start</code> in the <code>ShopEase-Ecommerce</code> directory to inject live faults, or switch to the <em>Internal Simulator</em> in the top header.
              </div>
            )}

            {/* Real Customer Traffic Generator Option */}
            {isShopEase && isConnected && (
              <div style={{
                marginBottom: '20px',
                padding: '18px 22px',
                background: workloadStatus?.is_running ? 'rgba(244, 63, 94, 0.05)' : '#f0fdf4',
                border: `1.5px solid ${workloadStatus?.is_running ? 'rgba(244, 63, 94, 0.4)' : '#bbf7d0'}`,
                borderRadius: '10px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '1.02rem', color: 'var(--text-main)' }}>
                        🛒 Realistic Customer Traffic Generator (No Fault Injection)
                      </strong>
                      <span className={`badge ${workloadStatus?.is_running ? 'badge-escalated' : 'badge-resolved'}`}>
                        {workloadStatus?.is_running ? `ACTIVE (${workloadStatus.active_workers || 35} WORKERS)` : 'STANDBY'}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.86rem', color: 'var(--text-muted)', maxWidth: '640px' }}>
                      Simulates authentic Indian lifestyle customer browsing, multi-keyword searches, and checkout orders. 
                      Multi-client search traffic naturally drives PostgreSQL connection contention and latency degradation.
                    </p>
                    {workloadStatus?.is_running && (
                      <div style={{ marginTop: '8px', display: 'flex', gap: '14px', fontSize: '0.82rem', color: 'var(--text-main)', flexWrap: 'wrap' }}>
                        <span><strong>Requests:</strong> {workloadStatus.total_requests}</span>
                        <span><strong>Throughput:</strong> {workloadStatus.current_rps} RPS</span>
                        <span><strong>P99 Latency:</strong> {workloadStatus.p99_latency_ms} ms</span>
                        <span><strong>Error Rate:</strong> {workloadStatus.error_rate_pct}%</span>
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    className={`btn btn-sm ${workloadStatus?.is_running ? 'btn-danger' : 'btn-primary'}`}
                    onClick={onToggleWorkload}
                    style={{ fontWeight: 600, padding: '8px 16px' }}
                  >
                    {workloadStatus?.is_running ? '⏹️ Stop Customer Traffic' : '🚀 Launch Customer Workload (35x)'}
                  </button>
                </div>
              </div>
            )}

            {/* Scenario Pills Selector */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px', marginBottom: '22px' }}>
              {catalog.map((sc, idx) => {
                const isSelected = selectedScenarioIndex === idx;
                const isActive = activeFaults.includes(sc.fault_type);
                return (
                  <div
                    key={sc.fault_type}
                    onClick={() => {
                      setSelectedScenarioIndex(idx);
                      setCurrentStep(1);
                    }}
                    style={{
                      background: isSelected ? 'var(--accent-teal-light)' : '#f8fafc',
                      border: `1.5px solid ${isSelected ? 'var(--accent-teal-dark)' : (isActive ? 'var(--status-red-border)' : 'var(--border-subtle)')}`,
                      borderRadius: '8px',
                      padding: '14px 16px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <span className="badge" style={{ background: '#ffffff', color: '#0369a1', border: '1px solid #bae6fd' }}>
                        {sc.target_service}
                      </span>
                      {isActive && <span className="badge badge-escalated" style={{ fontSize: '0.7rem' }}>Running</span>}
                    </div>
                    <strong style={{ fontSize: '0.95rem', color: isSelected ? 'var(--accent-teal-dark)' : 'var(--text-main)' }}>
                      {sc.name}
                    </strong>
                  </div>
                );
              })}
            </div>

            {/* Selected Scenario Details & Trigger Action */}
            {selectedScenario && (
              <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '14px' }}>
                  <div>
                    <h5 style={{ fontSize: '1.1rem', color: 'var(--text-main)', fontWeight: 700 }}>{selectedScenario.name}</h5>
                    <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>Target Service: <code>{selectedScenario.target_service}</code></div>
                  </div>
                  <div>
                    {isSelectedFaultActive ? (
                      <button
                        className="btn btn-danger"
                        onClick={() => onResetFault(selectedScenario.fault_type)}
                      >
                        Reset This Fault Scenario
                      </button>
                    ) : (
                      <button
                        className="btn btn-primary btn-lg"
                        onClick={handleTriggerCurrentScenario}
                      >
                        ⚡ Inject Fault Scenario
                      </button>
                    )}
                  </div>
                </div>

                <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', marginBottom: '16px', lineHeight: 1.5 }}>
                  {selectedScenario.description}
                </p>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px', fontSize: '0.86rem' }}>
                  <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', padding: '12px 16px', borderRadius: '6px' }}>
                    <span style={{ color: 'var(--status-amber-text)', fontWeight: 700, display: 'block', marginBottom: '4px' }}>
                      Expected Symptoms:
                    </span>
                    <span style={{ color: 'var(--text-body)' }}>{selectedScenario.symptoms}</span>
                  </div>
                  <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', padding: '12px 16px', borderRadius: '6px' }}>
                    <span style={{ color: 'var(--accent-teal-dark)', fontWeight: 700, display: 'block', marginBottom: '4px' }}>
                      Target Allowlisted Action:
                    </span>
                    <code style={{ color: 'var(--accent-teal-dark)', fontWeight: 600 }}>{selectedScenario.expected_remediation}</code>
                  </div>
                </div>

                {isSelectedFaultActive && (
                  <div style={{ marginTop: '18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--status-red-bg)', border: '1px solid var(--status-red-border)', padding: '14px 18px', borderRadius: '8px' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--status-red-text)', fontWeight: 500 }}>
                      ⚠️ Fault is active! Telemetry error rates and logs are streaming. Ready to investigate.
                    </span>
                    <button
                      className="btn btn-primary"
                      onClick={() => setCurrentStep(3)}
                    >
                      Proceed to Evidence Scan →
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* STEP 3: SCAN TELEMETRY & DETECT INCIDENT */}
        {currentStep === 3 && (
          <div>
            <div style={{ marginBottom: '18px' }}>
              <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                Step 3 of 7: Telemetry Anomaly Scanning & Incident Creation
              </span>
              <h4 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                Scan Live Telemetry & Correlate Evidence
              </h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                The anomaly scanner analyzes real-time HTTP error rates, P99 latencies, pool utilization, and structured error logs.
              </p>
            </div>

            {/* Current Snapshot */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '22px' }}>
              <div className="kpi-chip">
                <span className="label">HTTP Error Rate</span>
                <span className="value" style={{ color: metrics.error_rate_pct > 2 ? 'var(--status-red-text)' : 'var(--status-green-text)' }}>
                  {metrics.error_rate_pct ?? '0.0'}%
                </span>
              </div>
              <div className="kpi-chip">
                <span className="label">P99 Latency</span>
                <span className="value" style={{ color: metrics.p99_latency_ms > 500 ? 'var(--status-red-text)' : 'var(--status-green-text)' }}>
                  {metrics.p99_latency_ms ?? '45.0'} ms
                </span>
              </div>
              <div className="kpi-chip">
                <span className="label">DB Connection Pool</span>
                <span className="value" style={{ color: metrics.db_pool_utilization_pct > 80 ? 'var(--status-red-text)' : 'var(--status-green-text)' }}>
                  {metrics.db_pool_utilization_pct ?? '15.0'}%
                </span>
              </div>
              <div className="kpi-chip">
                <span className="label">Active Faults</span>
                <span className="value" style={{ color: activeFaults.length > 0 ? 'var(--status-red-text)' : 'var(--status-green-text)' }}>
                  {activeFaults.length}
                </span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '14px', alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary btn-lg"
                onClick={onDetectAndInvestigate}
                disabled={isInvestigating}
              >
                {isInvestigating ? 'Correlating Telemetry & Running RCA...' : '🔍 Scan Telemetry & Correlate Evidence'}
              </button>
              {selectedIncident && (
                <button
                  className="btn btn-secondary btn-lg"
                  onClick={() => setCurrentStep(4)}
                >
                  View Active Incident ({selectedIncident.id}) →
                </button>
              )}
            </div>
          </div>
        )}

        {/* STEP 4 & 5: AI ROOT CAUSE & HISTORICAL PRECEDENTS */}
        {(currentStep === 4 || currentStep === 5) && (
          <div>
            {!selectedIncident ? (
              <div style={{ textAlign: 'center', padding: '30px' }}>
                <p style={{ color: 'var(--text-muted)' }}>No incident currently selected or generated.</p>
                <button className="btn btn-primary" style={{ marginTop: '12px' }} onClick={() => setCurrentStep(3)}>
                  Back to Step 3: Scan Telemetry
                </button>
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
                  <div>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '6px', flexWrap: 'wrap' }}>
                      <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)' }}>
                        Step {currentStep === 4 ? '4: Root Cause Diagnosis' : '5: Historical Precedents'}
                      </span>
                      <code>{selectedIncident.id}</code>
                      {renderStatusBadge(selectedIncident.status)}
                      {selectedIncident.is_active ? (
                        <span className="badge badge-escalated" style={{ fontSize: '0.74rem', fontWeight: 700 }}>
                          🔴 LIVE ACTIVE
                        </span>
                      ) : (
                        <span className="badge badge-simulation" style={{ fontSize: '0.74rem' }}>
                          📁 Historical Record
                        </span>
                      )}
                      <span className="badge" style={{ background: '#f1f5f9', color: '#475569', fontSize: '0.74rem' }}>
                        {selectedIncident.target_system === 'shopease' ? '🛒 ShopEase' : '🧪 Simulator'}
                      </span>
                    </div>
                    <h4 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)' }}>{selectedIncident.title}</h4>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      Culprit Service: <strong style={{ color: 'var(--text-main)' }}>{selectedIncident.culprit_service}</strong> | Severity: <strong>{selectedIncident.severity}</strong>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className={`btn btn-sm ${currentStep === 4 ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setCurrentStep(4)}
                    >
                      Root Cause Diagnosis
                    </button>
                    <button
                      className={`btn btn-sm ${currentStep === 5 ? 'btn-primary' : 'btn-secondary'}`}
                      onClick={() => setCurrentStep(5)}
                    >
                      Historical Matches ({selectedIncident.retrieved_cases?.length || 0})
                    </button>
                  </div>
                </div>

                {/* Sub-View: RCA Diagnosis */}
                {currentStep === 4 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ background: '#f8fafc', padding: '18px 20px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                          Suspected Root Cause
                        </span>
                        <span style={{ color: 'var(--status-green-text)', fontWeight: 700, fontSize: '0.9rem' }}>
                          Confidence: {((selectedIncident.confidence_score || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ fontSize: '0.94rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                        {selectedIncident.rca_summary || selectedIncident.suspected_root_cause || (
                          <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>
                            Root cause analysis in progress: correlating telemetry signals for {selectedIncident.culprit_service}...
                          </span>
                        )}
                      </p>
                      {selectedIncident.confidence_explanation && (
                        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '10px', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                          <strong>Confidence Calculation Explanation:</strong> {selectedIncident.confidence_explanation}
                        </div>
                      )}
                    </div>

                    {/* Corroborating Evidence Cards */}
                    {selectedIncident.evidence && selectedIncident.evidence.length > 0 && (
                      <div>
                        <div style={{ fontSize: '0.86rem', color: 'var(--text-main)', fontWeight: 600, marginBottom: '8px' }}>
                          Corroborating Telemetry & Log Evidence ({selectedIncident.evidence.length} Signals)
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
                          {selectedIncident.evidence.map((ev, i) => (
                            <div key={i} style={{ background: '#ffffff', padding: '12px 14px', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.84rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                                <span style={{ color: 'var(--status-amber-text)', fontWeight: 700 }}>{ev.type?.toUpperCase()}</span>
                                {ev.value && <code style={{ color: 'var(--status-red-text)' }}>{ev.value}</code>}
                              </div>
                              <div style={{ color: 'var(--text-body)' }}>{ev.detail || ev.message}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                      <button className="btn btn-primary" onClick={() => setCurrentStep(5)}>
                        Inspect Historical Precedent Matches →
                      </button>
                    </div>
                  </div>
                )}

                {/* Sub-View: Historical Precedents */}
                {currentStep === 5 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div style={{ background: 'var(--accent-teal-light)', border: '1px solid #99f6e4', padding: '14px 18px', borderRadius: '8px' }}>
                      <span style={{ fontSize: '0.88rem', color: 'var(--accent-teal-dark)' }}>
                        💡 <strong>Adaptive Retrieval at Work:</strong> Past post-mortems were evaluated against threshold θ = 0.55. Only high-confidence matches were admitted into the diagnostic context, filtering out irrelevant precedents.
                      </span>
                    </div>

                    {(!selectedIncident.retrieved_cases || selectedIncident.retrieved_cases.length === 0) ? (
                      <div style={{ padding: '28px', textAlign: 'center', background: '#f8fafc', borderRadius: '8px', border: '1px dashed var(--border-card)', color: 'var(--text-muted)' }}>
                        <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>🛡️</div>
                        <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>Zero Precedents Met Threshold (Novel Incident Mode)</strong>
                        <p style={{ fontSize: '0.86rem', marginTop: '4px', lineHeight: 1.4 }}>
                          Returning 0 cases is safe and intentional: it prevents misleading the investigation with unrelated historical precedents.
                        </p>
                      </div>
                    ) : (
                      selectedIncident.retrieved_cases.map((c) => (
                        <div key={c.id} style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '16px', boxShadow: 'var(--shadow-sm)' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <strong style={{ fontSize: '0.94rem', color: 'var(--text-main)' }}>{c.id}: {c.title}</strong>
                            <span style={{ color: 'var(--accent-teal-dark)', fontWeight: 700, fontSize: '0.9rem' }}>
                              Relevance Score: {(c.similarity_score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p style={{ fontSize: '0.88rem', color: 'var(--text-body)', marginBottom: '8px' }}>
                            {c.root_cause}
                          </p>
                          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                            Historical Fix: <code style={{ color: 'var(--accent-teal-dark)', fontWeight: 600 }}>{c.recommended_remediation}</code>
                          </div>
                          {c.matching_evidence && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '10px', fontSize: '0.78rem' }}>
                              <span style={{ color: 'var(--text-muted)' }}>Matched Tokens:</span>
                              {c.matching_evidence.matched_tokens?.map((tok, idx) => (
                                <span key={idx} style={{ background: '#f1f5f9', color: '#1e293b', padding: '1px 7px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>{tok}</span>
                              ))}
                              {c.matching_evidence.service_match && (
                                <span style={{ background: 'var(--status-green-bg)', color: 'var(--status-green-text)', padding: '1px 8px', borderRadius: '4px', border: '1px solid var(--status-green-border)', fontWeight: 600 }}>
                                  Service Affinity (+15%)
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      ))
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '10px' }}>
                      <button className="btn btn-primary" onClick={() => setCurrentStep(6)}>
                        Proceed to Human Approval Gate →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* STEP 6: HUMAN-IN-THE-LOOP APPROVAL GATE */}
        {currentStep === 6 && (
          <div>
            <div style={{ marginBottom: '18px' }}>
              <span className="badge" style={{ background: 'var(--status-amber-bg)', color: 'var(--status-amber-text)', marginBottom: '8px' }}>
                Step 6 of 7: Human Authorization Security Gate
              </span>
              <h4 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                Explicit Human Authorization Required
              </h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                Strict backend security rule: No automated remediation action can execute without explicit operator sign-off and allowlist validation.
              </p>
            </div>

            {selectedIncident ? (
              <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '22px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px', marginBottom: '18px' }}>
                  <div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Proposed Allowlisted Fix</div>
                    <code style={{ fontSize: '1.15rem', color: 'var(--accent-teal-dark)', fontWeight: 700 }}>{selectedIncident.proposed_action}</code>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginTop: '4px' }}>
                      Risk Level: <strong style={{ color: selectedIncident.risk_level === 'LOW' ? 'var(--status-green-text)' : 'var(--status-amber-text)' }}>{selectedIncident.risk_level}</strong> | Reversible: <span style={{ color: 'var(--status-green-text)', fontWeight: 600 }}>✓ Guaranteed</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '6px' }}>
                    {renderStatusBadge(selectedIncident.status)}
                    {selectedIncident.is_active ? (
                      <span className="badge badge-escalated" style={{ fontSize: '0.74rem', fontWeight: 700 }}>
                        🔴 LIVE ACTIVE
                      </span>
                    ) : (
                      <span className="badge badge-simulation" style={{ fontSize: '0.74rem' }}>
                        📁 Historical Record
                      </span>
                    )}
                  </div>
                </div>

                {selectedIncident.status === 'AWAITING_APPROVAL' ? (
                  <div style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', padding: '18px 20px', borderRadius: '8px' }}>
                    <label style={{ fontSize: '0.86rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '8px' }}>
                      Incident Commander / Operator Authorization Name:
                    </label>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <input
                        type="text"
                        value={approverName}
                        onChange={(e) => setApproverName(e.target.value)}
                        style={{ flex: 1, minWidth: '240px' }}
                      />
                      <button
                        className="btn btn-success btn-lg"
                        onClick={() => onApproveRemediation(selectedIncident.id, true, approverName)}
                        disabled={isApproving}
                      >
                        {isApproving ? 'Authorizing...' : '✓ Authorize & Approve Fix'}
                      </button>
                      <button
                        className="btn btn-danger btn-lg"
                        onClick={() => onApproveRemediation(selectedIncident.id, false, approverName, 'Operator rejected')}
                        disabled={isApproving}
                      >
                        ✕ Reject
                      </button>
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--accent-teal-light)', border: '1px solid #99f6e4', padding: '14px 18px', borderRadius: '8px' }}>
                    <span style={{ fontSize: '0.9rem', color: 'var(--accent-teal-dark)', fontWeight: 500 }}>
                      ✓ Action authorized by <strong>{selectedIncident.approved_by || 'Operator'}</strong>. Ready for safe execution.
                    </span>
                    <button className="btn btn-primary" onClick={() => setCurrentStep(7)}>
                      Proceed to Execution & Recovery Verification →
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No incident loaded.</p>
            )}
          </div>
        )}

        {/* STEP 7: CLOSED-LOOP EXECUTION & SLO VERIFICATION */}
        {currentStep === 7 && (
          <div>
            <div style={{ marginBottom: '18px' }}>
              <span className="badge" style={{ background: 'var(--status-green-bg)', color: 'var(--status-green-text)', marginBottom: '8px' }}>
                Step 7 of 7: Allowlisted Execution & Independent SLO Verification
              </span>
              <h4 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--text-main)', marginTop: '4px' }}>
                Allowlisted Execution & Independent Recovery Verification
              </h4>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                The platform executes the authorized action and independently verifies recovery against 5 SLO conditions. HTTP 200 alone is never accepted as recovery.
              </p>
            </div>

            {selectedIncident ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                {/* Execution Trigger Box */}
                {(selectedIncident.status === 'APPROVED' || selectedIncident.status === 'RETRYING') && (
                  <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: '10px', padding: '22px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                      <div>
                        <strong style={{ fontSize: '1.05rem', color: 'var(--text-main)' }}>Target Action: <code>{selectedIncident.proposed_action}</code></strong>
                        <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)' }}>Current Status: {renderStatusBadge(selectedIncident.status)}</div>
                      </div>

                      {/* Retry loop test toggle */}
                      <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.86rem', color: 'var(--text-body)', cursor: 'pointer', background: '#ffffff', padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)' }}>
                        <input
                          type="checkbox"
                          checked={simulateFail}
                          onChange={(e) => setSimulateFail(e.target.checked)}
                        />
                        <span>🧪 Simulate Ineffective Fix (Test Safe Retry Loop)</span>
                      </label>
                    </div>

                    <button
                      className="btn btn-primary btn-lg"
                      style={{ width: '100%' }}
                      onClick={() => onExecuteRemediation(selectedIncident.id, simulateFail)}
                      disabled={isExecuting}
                    >
                      {isExecuting ? 'Executing Allowlisted Fix & Sampling Recovery SLOs...' : '⚡ Execute Remediation & Independently Verify Recovery'}
                    </button>
                  </div>
                )}

                {/* Verification Results Display */}
                {selectedIncident.verification_details && (
                  <div style={{
                    background: selectedIncident.verification_details.status === 'PASSED' ? 'var(--status-green-bg)' : 'var(--status-red-bg)',
                    border: `1.5px solid ${selectedIncident.verification_details.status === 'PASSED' ? 'var(--status-green-border)' : 'var(--status-red-border)'}`,
                    borderRadius: '10px',
                    padding: '22px'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                      <strong style={{
                        fontSize: '1.1rem',
                        color: selectedIncident.verification_details.status === 'PASSED' ? 'var(--status-green-text)' : 'var(--status-red-text)'
                      }}>
                        Independent Recovery Verification: {selectedIncident.verification_details.status}
                      </strong>
                      {renderStatusBadge(selectedIncident.status)}
                    </div>

                    <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', marginBottom: '16px', lineHeight: 1.5 }}>
                      {selectedIncident.verification_details.details}
                    </p>

                    {/* 5 SLO Checks Pills */}
                    {selectedIncident.verification_details.slo_checks && (
                      <div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
                          Independent Verification Gates
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {Object.entries(selectedIncident.verification_details.slo_checks).map(([check, passed]) => (
                            <span
                              key={check}
                              className="badge"
                              style={{
                                background: passed ? '#ffffff' : '#ffffff',
                                color: passed ? 'var(--status-green-text)' : 'var(--status-red-text)',
                                border: `1px solid ${passed ? 'var(--status-green-border)' : 'var(--status-red-border)'}`,
                                fontSize: '0.8rem'
                              }}
                            >
                              {passed ? '✓' : '✕'} {check.replace(/_/g, ' ')}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedIncident.resolution_summary && (
                      <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid rgba(0,0,0,0.06)', fontSize: '0.9rem', color: 'var(--text-main)' }}>
                        <strong>Resolution Summary:</strong> {selectedIncident.resolution_summary}
                      </div>
                    )}
                  </div>
                )}

                {/* Reset or Run Next Demo */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '10px' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setCurrentStep(1)}
                  >
                    ← Test Another Failure Scenario
                  </button>
                  {selectedIncident.status === 'RESOLVED' && (
                    <span style={{ color: 'var(--status-green-text)', fontSize: '0.92rem', fontWeight: 600 }}>
                      🎉 Incident successfully closed with verified recovery!
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No incident loaded.</p>
            )}
          </div>
        )}
      </div>

      {/* Expandable Section: Live Telemetry Stream */}
      <div className="accordion-box">
        <div className="accordion-header" onClick={() => setShowLogs(!showLogs)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>📜</span>
            <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
              Live Telemetry & Error Logs Stream ({logs.length} events)
            </strong>
          </div>
          <span style={{ fontSize: '0.84rem', color: 'var(--accent-teal-dark)', fontWeight: 600 }}>
            {showLogs ? 'Hide Logs ▲' : 'Show Logs ▼'}
          </span>
        </div>
        {showLogs && (
          <div className="accordion-body" style={{ maxHeight: '260px', overflowY: 'auto', background: '#ffffff', fontSize: '0.84rem' }}>
            {logs.length === 0 ? (
              <div style={{ color: 'var(--text-muted)' }}>No recent log lines captured.</div>
            ) : (
              logs.map((l, idx) => {
                const isErr = l.level === 'ERROR' || l.level === 'CRITICAL';
                return (
                  <div key={idx} style={{ display: 'flex', gap: '12px', padding: '4px 0', borderBottom: '1px solid #f1f5f9' }}>
                    <span style={{ color: 'var(--text-muted)', minWidth: '70px' }}>
                      {l.timestamp ? l.timestamp.split('T')[1]?.slice(0, 8) : 'now'}
                    </span>
                    <span style={{ color: isErr ? 'var(--status-red-text)' : 'var(--status-green-text)', fontWeight: 600, minWidth: '55px' }}>
                      [{l.level}]
                    </span>
                    <span style={{ color: 'var(--accent-teal-dark)', minWidth: '130px', fontWeight: 500 }}>{l.service}</span>
                    <span style={{ color: isErr ? '#991b1b' : 'var(--text-body)' }}>{l.message}</span>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>

      {/* Expandable Section: Incident Archive / History */}
      <div className="accordion-box">
        <div className="accordion-header" onClick={() => setShowHistory(!showHistory)}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span>🗂️</span>
            <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
              Incident Archive & History ({incidents.length} recorded)
            </strong>
          </div>
          <span style={{ fontSize: '0.84rem', color: 'var(--accent-teal-dark)', fontWeight: 600 }}>
            {showHistory ? 'Hide Archive ▲' : 'Show Archive ▼'}
          </span>
        </div>
        {showHistory && (
          <div className="accordion-body" style={{ overflowX: 'auto', background: '#ffffff' }}>
            {incidents.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>No recorded incidents.</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID & Context</th>
                    <th>Target</th>
                    <th>Title</th>
                    <th>Culprit</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Retries</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map((inc) => (
                    <tr key={inc.id} style={{ background: inc.is_active ? 'rgba(239, 68, 68, 0.05)' : undefined }}>
                      <td>
                        <code>{inc.id}</code>
                        <div style={{ marginTop: '3px' }}>
                          {inc.is_active ? (
                            <span className="badge badge-escalated" style={{ fontSize: '0.68rem', padding: '1px 6px', fontWeight: 700 }}>
                              🔴 LIVE ACTIVE
                            </span>
                          ) : (
                            <span className="badge badge-simulation" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                              📁 Archived
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className="badge" style={{ fontSize: '0.74rem', background: inc.target_system === 'shopease' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(99, 102, 241, 0.1)', color: inc.target_system === 'shopease' ? '#059669' : '#4f46e5' }}>
                          {inc.target_system === 'shopease' ? '🛒 ShopEase' : '🧪 Simulator'}
                        </span>
                      </td>
                      <td style={{ maxWidth: '240px' }}>{inc.title}</td>
                      <td><span style={{ color: 'var(--accent-teal-dark)', fontWeight: 500 }}>{inc.culprit_service}</span></td>
                      <td>{renderStatusBadge(inc.status)}</td>
                      <td>{((inc.confidence_score || 0) * 100).toFixed(0)}%</td>
                      <td>{inc.retry_count}/{inc.max_retries}</td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => {
                            onSelectIncident(inc.id);
                            setCurrentStep(4);
                          }}
                        >
                          Load into Inspector
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
