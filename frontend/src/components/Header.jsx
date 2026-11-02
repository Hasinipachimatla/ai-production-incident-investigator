import React from 'react';

export default function Header({
  activeTab,
  setActiveTab,
  telemetry,
  activeFaults: activeFaultsProp = null,
  onResetAllFaults,
  isResetting,
  targetEnvironment = 'shopease',
  setTargetEnvironment,
  shopeaseHealth,
  monitoringStatus,
  workloadStatus = null,
  onToggleWorkload = null
}) {
  const metrics = telemetry?.metrics || {};
  const activeFaults = Array.isArray(activeFaultsProp)
    ? activeFaultsProp.length
    : (typeof activeFaultsProp === 'number'
      ? activeFaultsProp
      : (telemetry?.metrics?.active_fault_count ?? (telemetry?.metrics?.raw_shopease?.faults?.activeCount ?? (Array.isArray(telemetry?.activeFaults) ? telemetry.activeFaults.length : 0))));
  const isAnomaly = telemetry?.anomaly_detected || activeFaults > 0;
  const isShopEase = targetEnvironment === 'shopease';
  const isConnected = isShopEase ? Boolean(shopeaseHealth?.connected) : true;

  return (
    <header className="glass-panel app-header">
      <div className="header-top">
        <div className="title-area">
          <div className="logo-badge">AI</div>
          <div className="title-text">
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
              <h1>AI Production Incident Investigator</h1>
              <span className={`badge ${isShopEase ? 'badge-resolved' : 'badge-simulation'}`}>
                {isShopEase ? '🛒 Live ShopEase Marketplace' : '🧪 Controlled Microservice Simulator'}
              </span>
            </div>
            <p>Adaptive Historical Incident Retrieval & Human-Approved Closed-Loop Remediation</p>
          </div>
        </div>

        <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          {/* Target Environment Switcher */}
          <div style={{
            display: 'inline-flex',
            background: '#f1f5f9',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)'
          }}>
            <button
              type="button"
              className={`btn btn-sm ${isShopEase ? 'btn-primary' : ''}`}
              style={{
                borderRadius: '6px',
                padding: '5px 12px',
                fontSize: '0.8rem',
                fontWeight: 600,
                background: isShopEase ? undefined : 'transparent',
                color: isShopEase ? undefined : 'var(--text-muted)',
                boxShadow: isShopEase ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
              onClick={() => setTargetEnvironment && setTargetEnvironment('shopease')}
              title="Target live Express + PostgreSQL ShopEase application (port 5000)"
            >
              🛒 Live ShopEase {isConnected ? '🟢' : '🔴'}
            </button>
            <button
              type="button"
              className={`btn btn-sm ${!isShopEase ? 'btn-primary' : ''}`}
              style={{
                borderRadius: '6px',
                padding: '5px 12px',
                fontSize: '0.8rem',
                fontWeight: 600,
                background: !isShopEase ? undefined : 'transparent',
                color: !isShopEase ? undefined : 'var(--text-muted)',
                boxShadow: !isShopEase ? '0 1px 3px rgba(0,0,0,0.1)' : 'none'
              }}
              onClick={() => setTargetEnvironment && setTargetEnvironment('simulator')}
              title="Target internal in-memory microservices fault simulator"
            >
              🧪 Simulator
            </button>
          </div>

          {activeFaults > 0 && (
            <button
              className="btn btn-danger btn-sm"
              onClick={onResetAllFaults}
              disabled={isResetting}
            >
              {isResetting ? 'Restoring...' : `Reset Active Faults (${activeFaults})`}
            </button>
          )}

          <div className={`badge ${isAnomaly ? 'badge-escalated' : (isConnected ? 'badge-resolved' : 'badge-escalated')}`}>
            <span className="badge-dot" />
            {isAnomaly
              ? `SYSTEM ANOMALY (${activeFaults} ACTIVE)`
              : (isConnected ? (isShopEase ? 'SHOPEASE HEALTHY (:5000)' : 'SIMULATOR NOMINAL') : 'SHOPEASE OFFLINE (:5000)')
            }
          </div>

          {isShopEase && monitoringStatus && (
            <div
              className={`badge ${monitoringStatus.is_running ? 'badge-resolved' : 'badge-simulation'}`}
              title={`Autonomous daemon polling ShopEase every ${monitoringStatus.polling_interval_seconds}s (sustained threshold=${monitoringStatus.consecutive_threshold}). Polls recorded: ${monitoringStatus.polls_count}`}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <span className="badge-dot" style={{ background: monitoringStatus.is_running ? '#22c55e' : '#f59e0b' }} />
              <span>Daemon: {monitoringStatus.is_running ? 'POLLING' : 'PAUSED'} ({monitoringStatus.polling_interval_seconds}s)</span>
            </div>
          )}

          {isShopEase && workloadStatus && (
            <div
              className={`badge ${workloadStatus.is_running ? 'badge-escalated' : 'badge-resolved'}`}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: onToggleWorkload ? 'pointer' : 'default' }}
              onClick={onToggleWorkload}
              title={workloadStatus.is_running ? `Click to stop customer traffic. Active workers: ${workloadStatus.active_workers || 35}, RPS: ${workloadStatus.current_rps}` : 'Click to launch realistic customer workload (35 concurrent sessions)'}
            >
              <span className="badge-dot" style={{ background: workloadStatus.is_running ? '#ef4444' : '#10b981' }} />
              <span>Traffic: {workloadStatus.is_running ? `RUNNING (${workloadStatus.current_rps || 0} RPS)` : 'STANDBY'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Live Telemetry KPI Strip */}
      <div className="telemetry-strip">
        <div className={`kpi-chip ${metrics.p99_latency_ms > 500 ? 'anomaly' : 'nominal'}`}>
          <span className="label">P99 Response Time</span>
          <span className="value">{metrics.p99_latency_ms ? `${metrics.p99_latency_ms} ms` : '45.0 ms'}</span>
        </div>

        <div className={`kpi-chip ${metrics.error_rate_pct > 2.0 ? 'anomaly' : 'nominal'}`}>
          <span className="label">HTTP Error Rate</span>
          <span className="value">{metrics.error_rate_pct !== undefined ? `${metrics.error_rate_pct}%` : '0.15%'}</span>
        </div>

        <div className={`kpi-chip ${metrics.db_pool_utilization_pct > 80 ? 'anomaly' : 'nominal'}`}>
          <span className="label">Database Connection Pool</span>
          <span className="value">{metrics.db_pool_utilization_pct !== undefined ? `${metrics.db_pool_utilization_pct}%` : '18.0%'}</span>
        </div>

        <div className={`kpi-chip ${metrics.cache_hit_rate_pct < 60 ? 'warning' : 'nominal'}`}>
          <span className="label">Cache Hit Ratio</span>
          <span className="value">{metrics.cache_hit_rate_pct !== undefined ? `${metrics.cache_hit_rate_pct}%` : '96.5%'}</span>
        </div>

        <div className={`kpi-chip ${activeFaults > 0 ? 'anomaly' : 'nominal'}`}>
          <span className="label">Active Injected Faults</span>
          <span className="value">{activeFaults}</span>
        </div>
      </div>

      {/* Main Tab Navigation */}
      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => setActiveTab('home')}
        >
          🧭 Overview & Guide
        </button>

        <button
          className={`tab-btn ${activeTab === 'investigation' ? 'active' : ''}`}
          onClick={() => setActiveTab('investigation')}
        >
          ⚡ Guided Incident Investigation
        </button>

        <button
          className={`tab-btn ${activeTab === 'retrieval' ? 'active' : ''}`}
          onClick={() => setActiveTab('retrieval')}
        >
          🔬 Adaptive Retrieval (Research Gap 1)
        </button>

        <button
          className={`tab-btn ${activeTab === 'experiments' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiments')}
        >
          📊 Benchmark Experiments
        </button>

        <button
          className={`tab-btn ${activeTab === 'dataset' ? 'active' : ''}`}
          onClick={() => setActiveTab('dataset')}
        >
          📁 Datasets & Pipeline
        </button>
      </nav>
    </header>
  );
}
