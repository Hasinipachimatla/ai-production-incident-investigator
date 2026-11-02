import React, { useState } from 'react';

export default function FaultControlPanel({
  catalog,
  activeFaults,
  onTriggerFault,
  onResetFault,
  telemetry,
  onInvestigateNow,
  isShopEase = false,
  workloadStatus = null,
  onToggleWorkload = null
}) {
  const [triggeringFault, setTriggeringFault] = useState(null);

  const handleToggle = async (faultType, isActive) => {
    setTriggeringFault(faultType);
    try {
      if (isActive) {
        await onResetFault(faultType);
      } else {
        await onTriggerFault(faultType);
      }
    } finally {
      setTriggeringFault(null);
    }
  };

  const logs = telemetry?.logs || [];
  const isWorkloadRunning = Boolean(workloadStatus?.is_running);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Real Customer Workload Generator Card (ShopEase live environment) */}
      {isShopEase && (
        <div className="glass-panel" style={{
          padding: '24px',
          borderLeft: isWorkloadRunning ? '4px solid var(--accent-rose)' : '4px solid var(--accent-teal)',
          background: isWorkloadRunning ? 'rgba(244, 63, 94, 0.04)' : undefined
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
            <div style={{ maxWidth: '650px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                <h3 style={{ fontSize: '1.1rem', margin: 0 }}>🛒 Realistic Customer Traffic Generator</h3>
                <span className={`badge ${isWorkloadRunning ? 'badge-escalated' : 'badge-resolved'}`}>
                  {isWorkloadRunning ? `ACTIVE (${workloadStatus?.active_workers || 35} WORKERS)` : 'STANDBY'}
                </span>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: '1.5', margin: 0 }}>
                Generates live concurrent customer traffic (catalog browsing, text searches, and order transactions) against ShopEase 
                <strong> without injecting artificial faults</strong>. Heavy multi-client search traffic naturally induces PostgreSQL 
                connection pool contention, driving response latency above the 500ms SLO to test autonomous detection and operational rate limiting.
              </p>
              {isWorkloadRunning && (
                <div style={{ marginTop: '12px', display: 'flex', gap: '16px', fontSize: '0.85rem', color: 'var(--text-main)', flexWrap: 'wrap' }}>
                  <span><strong>Requests:</strong> {workloadStatus?.total_requests || 0}</span>
                  <span><strong>Throughput:</strong> {workloadStatus?.current_rps || 0} RPS</span>
                  <span><strong>P99 Latency:</strong> {workloadStatus?.p99_latency_ms || 0} ms</span>
                  <span><strong>Error Rate:</strong> {workloadStatus?.error_rate_pct || 0}%</span>
                </div>
              )}
            </div>

            <button
              type="button"
              className={`btn ${isWorkloadRunning ? 'btn-danger' : 'btn-primary'}`}
              onClick={onToggleWorkload}
              style={{ minWidth: '220px' }}
            >
              {isWorkloadRunning ? '⏹️ Stop Customer Traffic' : '🚀 Launch Customer Workload (35x)'}
            </button>
          </div>
        </div>
      )}

      {/* Intro Research Notice */}
      <div className="glass-panel" style={{ padding: '20px 24px', borderLeft: '4px solid var(--accent-indigo)' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '6px' }}>Controlled Microservice Fault Scenarios</h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Simulates controlled, reversible production failure modes without destructive side-effects. 
          Triggering a scenario injects realistic telemetry metrics and structured error logs to test autonomous closed-loop diagnosis and recovery.
        </p>
      </div>

      {/* Scenarios Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
        gap: '20px'
      }}>
        {catalog.map((scenario) => {
          const isActive = activeFaults.includes(scenario.fault_type);
          const isBusy = triggeringFault === scenario.fault_type;

          return (
            <div
              key={scenario.fault_type}
              className="glass-panel"
              style={{
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                borderColor: isActive ? 'rgba(244, 63, 94, 0.4)' : 'var(--border-subtle)',
                boxShadow: isActive ? '0 0 20px rgba(244, 63, 94, 0.15)' : 'none'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <span className="badge" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#a5b4fc', borderColor: 'rgba(99, 102, 241, 0.3)' }}>
                    {scenario.target_service}
                  </span>
                  {isActive && (
                    <span className="badge badge-escalated">
                      <span className="badge-dot" /> ACTIVE INJECTION
                    </span>
                  )}
                </div>

                <h4 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '8px' }}>
                  {scenario.name}
                </h4>

                <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)', marginBottom: '14px', minHeight: '40px' }}>
                  {scenario.description}
                </p>

                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px 12px', borderRadius: '6px', marginBottom: '16px' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '2px' }}>Observed Symptoms</div>
                  <div style={{ fontSize: '0.82rem', color: '#e2e8f0' }}>{scenario.symptoms}</div>
                </div>

                <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
                  Target Allowlisted Fix: <code style={{ color: 'var(--accent-cyan)' }}>{scenario.expected_remediation}</code>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                <button
                  className={`btn ${isActive ? 'btn-danger' : 'btn-primary'}`}
                  style={{ flex: 1 }}
                  onClick={() => handleToggle(scenario.fault_type, isActive)}
                  disabled={isBusy}
                >
                  {isBusy ? 'Updating...' : (isActive ? 'Reset Fault' : 'Trigger Fault Scenario')}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Log Stream & Auto-Investigation Trigger */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Live Telemetry Log Stream</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Real-time structured logs from application services</p>
          </div>

          <button
            className="btn btn-accent"
            onClick={onInvestigateNow}
          >
            🚀 Scan Telemetry & Trigger AI Investigation
          </button>
        </div>

        <div style={{
          background: '#050811',
          border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: '8px',
          padding: '14px',
          maxHeight: '260px',
          overflowY: 'auto',
          fontSize: '0.84rem'
        }}>
          {logs.length === 0 ? (
            <div style={{ color: 'var(--text-dim)', padding: '12px 0' }}>No recent log lines recorded.</div>
          ) : (
            logs.map((l, idx) => {
              const isErr = l.level === 'ERROR' || l.level === 'CRITICAL';
              const isWarn = l.level === 'WARN';
              return (
                <div key={idx} style={{ display: 'flex', gap: '12px', padding: '4px 0', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                  <span style={{ color: 'var(--text-dim)', fontSize: '0.76rem', minWidth: '70px' }}>
                    {l.timestamp ? l.timestamp.split('T')[1]?.slice(0, 8) : 'now'}
                  </span>
                  <span style={{
                    color: isErr ? 'var(--accent-rose)' : (isWarn ? 'var(--accent-amber)' : 'var(--accent-emerald)'),
                    fontWeight: 600,
                    minWidth: '55px'
                  }}>
                    [{l.level}]
                  </span>
                  <span style={{ color: 'var(--accent-cyan)', minWidth: '130px' }}>{l.service}</span>
                  <span style={{ color: isErr ? '#fecdd3' : '#cbd5e1' }}>{l.message}</span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
