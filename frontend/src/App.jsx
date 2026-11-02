import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import HomeGuidedDemo from './components/HomeGuidedDemo';
import GuidedInvestigation from './components/GuidedInvestigation';
import RetrievalWorkbench from './components/RetrievalWorkbench';
import ExperimentWorkbench from './components/ExperimentWorkbench';
import DatasetManager from './components/DatasetManager';
import { api } from './api';

const SHOPEASE_CATALOG = [
  {
    fault_type: 'db_exhaustion',
    name: 'Database Connection Pool Exhaustion',
    target_service: 'postgresql-database',
    description: 'Exhausts the PostgreSQL connection pool by holding client connections, inducing QueuePool timeout errors and 503 HTTP responses.',
    symptoms: 'DB Pool 20/20 (100%), QueuePool connection timeouts, HTTP 503 on catalog queries.',
    expected_remediation: 'restart_connection_pool'
  },
  {
    fault_type: 'high_latency',
    name: 'High API Latency Cascade',
    target_service: 'catalog-service',
    description: 'Injects an artificial +2000ms delay into product catalog endpoints, simulating downstream worker starvation.',
    symptoms: 'P95 latency spikes to >2000ms, X-Fault-Injected header present, slow searches.',
    expected_remediation: 'rate_limit_throttle'
  },
  {
    fault_type: 'service_error_spike',
    name: 'Checkout Order 500 Error Spike',
    target_service: 'order-service',
    description: 'Forces HTTP 500 Internal Server Errors on order checkout transactions, causing instant error rate SLO breaches.',
    symptoms: 'HTTP 500 on /api/orders, error rate spikes > 30%, checkout transactions fail.',
    expected_remediation: 'rollback_config_flag'
  },
  {
    fault_type: 'cache_failure',
    name: 'Cache Invalidation Outage',
    target_service: 'cache-service',
    description: 'Marks cache service UNAVAILABLE, bypassing cache lookups and logging critical miss-storm errors.',
    symptoms: 'Cache hit ratio collapses to 0%, X-Cache: UNAVAILABLE headers, direct database fallback.',
    expected_remediation: 'flush_and_warm_cache'
  },
  {
    fault_type: 'circuit_breaker_trip',
    name: 'Circuit Breaker Trip (Inventory)',
    target_service: 'inventory-service',
    description: 'Forces failures in inventory dependency until circuit breaker trips from CLOSED to OPEN, fast-failing traffic.',
    symptoms: 'Circuit breaker state OPEN, 503 circuit open rejections, fallback static responses.',
    expected_remediation: 'reset_circuit_breaker'
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [targetEnvironment, setTargetEnvironment] = useState('shopease');
  const [shopeaseHealth, setShopeaseHealth] = useState(null);
  const [monitoringStatus, setMonitoringStatus] = useState(null);
  const [workloadStatus, setWorkloadStatus] = useState(null);
  const [simulatorCatalog, setSimulatorCatalog] = useState([]);
  const [telemetry, setTelemetry] = useState(null);
  const [activeFaults, setActiveFaults] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [experimentReport, setExperimentReport] = useState(null);
  const [datasetStats, setDatasetStats] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [toast, setToast] = useState(null);

  // Action busy states
  const [isResetting, setIsResetting] = useState(false);
  const [isInvestigating, setIsInvestigating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isRunningExp, setIsRunningExp] = useState(false);
  const [isImporting, setIsImporting] = useState(false);

  const isShopEase = targetEnvironment === 'shopease';
  const currentCatalog = isShopEase ? SHOPEASE_CATALOG : simulatorCatalog;
  const isConnected = isShopEase ? Boolean(shopeaseHealth?.connected) : true;

  const hasActiveAnomaly = isShopEase
    ? Boolean(telemetry?.anomaly_detected || (activeFaults && activeFaults.length > 0) || monitoringStatus?.active_incident_id)
    : Boolean(telemetry?.anomaly_detected || (activeFaults && activeFaults.length > 0));

  const currentlyActiveIncident = hasActiveAnomaly ? (
    incidents.find((i) => {
      const isTargetMatch = isShopEase ? i.target_system === 'shopease' : (i.target_system !== 'shopease' || !i.target_system);
      if (!isTargetMatch) return false;
      if (isShopEase && monitoringStatus?.active_incident_id && i.id === monitoringStatus.active_incident_id) return true;
      if (i.is_active) return true;
      return ['DETECTED', 'INVESTIGATING', 'AWAITING_APPROVAL', 'APPROVED', 'REMEDIATING', 'VERIFYING', 'RETRYING'].includes(i.status);
    }) || null
  ) : null;

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4500);
  };

  // Poll Telemetry & Active Faults according to active target environment
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        if (targetEnvironment === 'shopease') {
          // Check ShopEase health, telemetry snapshot, faults, daemon status, and customer workload
          const [health, snap, faultsData, monData, workData, incList] = await Promise.all([
            api.getShopEaseHealth().catch(() => ({ connected: false })),
            api.getShopEaseSnapshot().catch(() => null),
            api.getShopEaseFaults().catch(() => ({ activeFaults: [] })),
            api.getMonitoringStatus().catch(() => null),
            api.getWorkloadStatus().catch(() => null),
            api.listIncidents().catch(() => null)
          ]);

          setShopeaseHealth(health);
          if (snap) {
            setTelemetry(snap);
          }
          if (faultsData?.activeFaults) {
            setActiveFaults(faultsData.activeFaults);
          }
          if (monData?.monitoring) {
            setMonitoringStatus(monData.monitoring);
          }
          if (workData?.workload) {
            setWorkloadStatus(workData.workload);
          }
          if (incList) {
            setIncidents(incList);
          }
        } else {
          // Internal Simulator
          const [data, act, incList] = await Promise.all([
            api.getTelemetryOverview().catch(() => null),
            api.getActiveFaults().catch(() => ({ active_faults: [] })),
            api.listIncidents().catch(() => null)
          ]);
          if (data) setTelemetry(data);
          if (act) setActiveFaults(act.active_faults || []);
          if (incList) setIncidents(incList);
        }
      } catch (err) {
        console.error('Failed to fetch telemetry:', err);
      }
    };

    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3000);
    return () => clearInterval(interval);
  }, [targetEnvironment]);

  // Initial Data Load
  useEffect(() => {
    const initData = async () => {
      try {
        const [simCat, incList, stats, prev, lastExp, activeInc] = await Promise.all([
          api.getFaultCatalog().catch(() => []),
          api.listIncidents().catch(() => []),
          api.getDatasetStats().catch(() => null),
          api.previewDataset().catch(() => null),
          api.getLastExperimentResults().catch(() => null),
          api.getActiveIncident(targetEnvironment).catch(() => null)
        ]);

        setSimulatorCatalog(simCat);
        setIncidents(incList || []);
        setDatasetStats(stats);
        if (prev) setPreviewData(prev);
        if (lastExp) setExperimentReport(lastExp);
        if (activeInc?.id) {
          setSelectedIncident(activeInc);
        } else {
          // Healthy baseline: start clean at Step 1 rather than locking into a historical incident
          setSelectedIncident(null);
        }
      } catch (err) {
        console.error('Initial load error:', err);
      }
    };

    initData();
  }, []);

  // Auto-hydrate incident details if selectedIncident is missing detail properties
  useEffect(() => {
    if (selectedIncident?.id && (!selectedIncident.evidence || !selectedIncident.rca_summary)) {
      api.getIncident(selectedIncident.id)
        .then(fullInc => setSelectedIncident(fullInc))
        .catch(err => console.error('Failed to hydrate incident detail:', err));
    }
  }, [selectedIncident?.id]);

  // Fault Actions
  const handleTriggerFault = async (faultType) => {
    try {
      if (isShopEase) {
        const params = faultType === 'high_latency' ? { delayMs: 2000 } : {};
        await api.injectShopEaseFault(faultType, params);
        const f = await api.getShopEaseFaults().catch(() => ({ activeFaults: [faultType] }));
        setActiveFaults(f.activeFaults || [faultType]);
        const snap = await api.getShopEaseSnapshot().catch(() => null);
        if (snap) setTelemetry(snap);
        showToast(`ShopEase fault '${faultType}' injected! Telemetry anomalies generated.`, 'error');
      } else {
        await api.triggerFault(faultType);
        const act = await api.getActiveFaults();
        setActiveFaults(act.active_faults || []);
        const t = await api.getTelemetryOverview();
        setTelemetry(t);
        showToast(`Controlled fault '${faultType}' injected into Simulator!`, 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleResetFault = async (faultType) => {
    try {
      if (isShopEase) {
        await api.disableShopEaseFault(faultType);
        const f = await api.getShopEaseFaults().catch(() => ({ activeFaults: [] }));
        setActiveFaults(f.activeFaults || []);
        const snap = await api.getShopEaseSnapshot().catch(() => null);
        if (snap) setTelemetry(snap);
        showToast(`ShopEase fault '${faultType}' disabled.`, 'success');
      } else {
        await api.resetFault(faultType);
        const act = await api.getActiveFaults();
        setActiveFaults(act.active_faults || []);
        const t = await api.getTelemetryOverview();
        setTelemetry(t);
        showToast(`Simulator fault '${faultType}' reset.`, 'success');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleResetAllFaults = async () => {
    setIsResetting(true);
    try {
      if (isShopEase) {
        await api.resetShopEaseFaults();
        setActiveFaults([]);
        const snap = await api.getShopEaseSnapshot().catch(() => null);
        if (snap) setTelemetry(snap);
        showToast('All ShopEase faults cleared. System restored to healthy baseline.', 'success');
      } else {
        await api.resetAllFaults();
        setActiveFaults([]);
        const t = await api.getTelemetryOverview();
        setTelemetry(t);
        showToast('All simulator faults cleared. Baseline restored.', 'success');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsResetting(false);
    }
  };

  // Real Customer Workload Controls
  const handleToggleWorkload = async () => {
    try {
      if (workloadStatus?.is_running) {
        await api.stopWorkload();
        setWorkloadStatus(prev => (prev ? { ...prev, is_running: false } : null));
        showToast('Customer traffic generator stopped.', 'info');
      } else {
        await api.startWorkload({ concurrency: 35, ramp_seconds: 5.0, delay_sec: 0.03 });
        setWorkloadStatus(prev => (prev ? { ...prev, is_running: true } : { is_running: true }));
        showToast('Customer workload generator started with 35 concurrent sessions.', 'success');
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Autonomous Detection & RCA Investigation Flow
  const handleDetectAndInvestigate = async () => {
    setIsInvestigating(true);
    try {
      const res = await api.detectAndInvestigate(targetEnvironment);
      if (!res.incident_created) {
        showToast(res.message, 'info');
      } else {
        const updatedList = await api.listIncidents();
        setIncidents(updatedList);
        setSelectedIncident(res.incident);
        setActiveTab('investigation');
        showToast(`Incident ${res.incident.id} created! AI RCA generated with ${((res.incident.confidence_score || 0) * 100).toFixed(0)}% confidence.`, 'warning');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsInvestigating(false);
    }
  };

  const handleSelectIncident = async (id) => {
    try {
      const inc = await api.getIncident(id);
      setSelectedIncident(inc);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Remediation Approval Gate
  const handleApproveRemediation = async (id, approved, approverName, reason) => {
    setIsApproving(true);
    try {
      const res = await api.approveRemediation(id, {
        approved,
        approver_name: approverName,
        rejection_reason: reason
      });
      setSelectedIncident(res.incident);
      const updatedList = await api.listIncidents();
      setIncidents(updatedList);
      showToast(res.message, approved ? 'success' : 'error');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsApproving(false);
    }
  };

  // Remediation Execution & Verification
  const handleExecuteRemediation = async (id, simulateFailure) => {
    setIsExecuting(true);
    try {
      const res = await api.executeRemediation(id, simulateFailure);
      setSelectedIncident(res.incident);
      const [updatedList, t, act] = await Promise.all([
        api.listIncidents(),
        api.getTelemetryOverview(),
        api.getActiveFaults()
      ]);
      setIncidents(updatedList);
      setTelemetry(t);
      setActiveFaults(act.active_faults || []);

      if (res.verification?.status === 'PASSED') {
        showToast(`Remediation verified! SLOs restored. Incident ${id} RESOLVED.`, 'success');
      } else {
        showToast(`Verification FAILED! SLOs breached. Incident remains OPEN for safe retry (${res.incident.retry_count}/${res.incident.max_retries}).`, 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsExecuting(false);
    }
  };

  // Retrieval Comparison
  const handleCompareRetrieval = async (payload) => {
    setIsComparing(true);
    try {
      const res = await api.compareRetrieval(payload);
      setComparisonResult(res);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsComparing(false);
    }
  };

  // Experiment Benchmark Run
  const handleRunExperiment = async (payload) => {
    setIsRunningExp(true);
    try {
      const res = await api.runExperiment(payload);
      setExperimentReport(res);
      showToast(`Evaluation completed! Evaluated ${res.num_queries} queries. Noise reduction: ${res.irrelevant_noise_reduction_pct}%.`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsRunningExp(false);
    }
  };

  // Kaggle Sample Dataset Import
  const handleImportSampleKaggle = async () => {
    setIsImporting(true);
    try {
      const res = await api.importKaggleSample();
      const stats = await api.getDatasetStats();
      setDatasetStats(stats);
      showToast(res.message, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsImporting(false);
    }
  };

  // Custom Dataset Upload
  const handleUploadDataset = async (formData) => {
    const res = await api.uploadDataset(formData);
    const stats = await api.getDatasetStats();
    setDatasetStats(stats);
    return res;
  };

  const getToastColors = (type) => {
    switch (type) {
      case 'error':
        return { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c' };
      case 'warning':
        return { bg: '#fffbeb', border: '#fde68a', text: '#b45309' };
      default:
        return { bg: '#f0fdf4', border: '#bbf7d0', text: '#15803d' };
    }
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '24px',
          zIndex: 2000,
          background: getToastColors(toast.type).bg,
          border: `1.5px solid ${getToastColors(toast.type).border}`,
          color: getToastColors(toast.type).text,
          padding: '12px 20px',
          borderRadius: '8px',
          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.04)',
          fontWeight: 600,
          fontSize: '0.88rem',
          maxWidth: '440px',
          animation: 'fadeIn 0.2s ease'
        }}>
          {toast.message}
        </div>
      )}

      {/* Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        telemetry={telemetry}
        activeFaults={activeFaults}
        onResetAllFaults={handleResetAllFaults}
        isResetting={isResetting}
        targetEnvironment={targetEnvironment}
        setTargetEnvironment={setTargetEnvironment}
        shopeaseHealth={shopeaseHealth}
        monitoringStatus={monitoringStatus}
        workloadStatus={workloadStatus}
        onToggleWorkload={handleToggleWorkload}
      />

      {/* Autonomous Incident Alert Banner OR Healthy Nominal Status Banner */}
      {currentlyActiveIncident ? (
        <div style={{
          background: 'linear-gradient(90deg, #991b1b 0%, #dc2626 100%)',
          color: '#ffffff',
          padding: '12px 24px',
          borderRadius: '8px',
          margin: '12px 24px 0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 14px rgba(220, 38, 38, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '1.6rem' }}>🚨</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', letterSpacing: '0.02em', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span>AUTONOMOUS INCIDENT DETECTED: {currentlyActiveIncident.title} ({currentlyActiveIncident.id})</span>
                <span className="badge badge-escalated" style={{ fontSize: '0.72rem', background: '#ffffff', color: '#dc2626', fontWeight: 700 }}>
                  LIVE ACTIVE ANOMALY
                </span>
              </div>
              <div style={{ fontSize: '0.84rem', opacity: 0.95, marginTop: '2px' }}>
                Culprit: <strong>{currentlyActiveIncident.culprit_service}</strong> | Proposed Allowlisted Action: <code>{currentlyActiveIncident.proposed_action}</code>
              </div>
            </div>
          </div>
          <button
            className="btn btn-sm"
            style={{
              background: '#ffffff',
              color: '#dc2626',
              fontWeight: 700,
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              whiteSpace: 'nowrap'
            }}
            onClick={() => {
              if (currentlyActiveIncident?.id) {
                handleSelectIncident(currentlyActiveIncident.id);
              }
              setActiveTab('investigation');
            }}
          >
            Review & Authorize Remediation →
          </button>
        </div>
      ) : (
        <div style={{
          background: isShopEase && !isConnected
            ? 'linear-gradient(90deg, #78350f 0%, #b45309 100%)'
            : 'linear-gradient(90deg, #064e3b 0%, #047857 100%)',
          color: '#ffffff',
          padding: '10px 24px',
          borderRadius: '8px',
          margin: '12px 24px 0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: isShopEase && !isConnected
            ? '0 4px 12px rgba(180, 83, 9, 0.2)'
            : '0 4px 12px rgba(4, 120, 87, 0.2)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.3rem' }}>{isShopEase && !isConnected ? '⚠️' : '🛡️'}</span>
            <div>
              <div style={{ fontWeight: 700, fontSize: '0.92rem', letterSpacing: '0.02em' }}>
                {isShopEase && !isConnected
                  ? 'SHOPEASE DISCONNECTED — PORT 5000'
                  : 'SYSTEM HEALTHY — NO ACTIVE INCIDENTS'}
              </div>
              <div style={{ fontSize: '0.82rem', opacity: 0.95, marginTop: '1px' }}>
                {isShopEase ? (
                  !isConnected ? (
                    <span>ShopEase is offline on port 5000. Start it in the ShopEase-Ecommerce directory to observe live traffic.</span>
                  ) : (
                    <span>ShopEase (:5000) telemetry nominal. 0 active faults, 0% error rate. Autonomous monitoring daemon active.</span>
                  )
                ) : (
                  <span>Internal microservice testbed nominal. 0 active faults. Select a fault scenario to initiate an investigation.</span>
                )}
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.8rem', opacity: 0.9 }}>
              Historical Records: {incidents.length}
            </span>
            <button
              className="btn btn-sm"
              style={{
                background: '#ffffff',
                color: isShopEase && !isConnected ? '#b45309' : '#047857',
                fontWeight: 600,
                padding: '6px 14px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                fontSize: '0.82rem'
              }}
              onClick={() => setActiveTab('investigation')}
            >
              Incident Stepper →
            </button>
          </div>
        </div>
      )}

      {/* Main Tab Views */}
      <main>
        {activeTab === 'home' && (
          <HomeGuidedDemo
            telemetry={telemetry}
            catalog={currentCatalog}
            activeFaults={activeFaults}
            incidents={incidents}
            onStartDemo={() => setActiveTab('investigation')}
            onNavigateTab={(tab) => setActiveTab(tab)}
            targetEnvironment={targetEnvironment}
            shopeaseHealth={shopeaseHealth}
            workloadStatus={workloadStatus}
            onToggleWorkload={handleToggleWorkload}
          />
        )}

        {activeTab === 'investigation' && (
          <GuidedInvestigation
            catalog={currentCatalog}
            activeFaults={activeFaults}
            telemetry={telemetry}
            incidents={incidents}
            selectedIncident={selectedIncident}
            onSelectIncident={handleSelectIncident}
            onTriggerFault={handleTriggerFault}
            onResetFault={handleResetFault}
            onResetAllFaults={handleResetAllFaults}
            onDetectAndInvestigate={handleDetectAndInvestigate}
            onApproveRemediation={handleApproveRemediation}
            onExecuteRemediation={handleExecuteRemediation}
            isInvestigating={isInvestigating}
            isExecuting={isExecuting}
            isApproving={isApproving}
            isResetting={isResetting}
            targetEnvironment={targetEnvironment}
            shopeaseHealth={shopeaseHealth}
            workloadStatus={workloadStatus}
            onToggleWorkload={handleToggleWorkload}
          />
        )}

        {activeTab === 'retrieval' && (
          <RetrievalWorkbench
            onCompare={handleCompareRetrieval}
            comparisonResult={comparisonResult}
            isComparing={isComparing}
          />
        )}

        {activeTab === 'experiments' && (
          <ExperimentWorkbench
            experimentReport={experimentReport}
            onRunExperiment={handleRunExperiment}
            isRunning={isRunningExp}
          />
        )}

        {activeTab === 'dataset' && (
          <DatasetManager
            datasetStats={datasetStats}
            onImportSampleKaggle={handleImportSampleKaggle}
            onUploadDataset={handleUploadDataset}
            isImporting={isImporting}
            previewData={previewData}
          />
        )}
      </main>
    </div>
  );
}
