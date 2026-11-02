const API_BASE = '/api';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = options.headers || {};
  
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (!response.ok) {
    let errMsg = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const errData = await response.json();
      if (errData.detail) {
        errMsg = errData.detail;
      }
    } catch {
      // fallback
    }
    throw new Error(errMsg);
  }

  return response.json();
}

export const api = {
  // Faults
  getFaultCatalog: () => request('/faults/catalog'),
  getActiveFaults: () => request('/faults/active'),
  triggerFault: (fault_type, parameters = {}) =>
    request('/faults/trigger', {
      method: 'POST',
      body: JSON.stringify({ fault_type, parameters })
    }),
  resetFault: (fault_type) =>
    request(`/faults/reset/${fault_type}`, { method: 'POST' }),
  resetAllFaults: () => request('/faults/reset-all', { method: 'POST' }),

  // Telemetry
  getTelemetryOverview: () => request('/telemetry/overview'),

  // Incidents
  listIncidents: (status, service) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (service) params.append('service', service);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/incidents${qs}`);
  },
  getIncident: (id) => request(`/incidents/${id}`),
  getActiveIncident: (target_system) => {
    const qs = target_system ? `?target_system=${target_system}` : '';
    return request(`/incidents/active${qs}`);
  },
  detectAndInvestigate: (source) => {
    const qs = source ? `?source=${source}` : '';
    return request(`/incidents/detect-and-investigate${qs}`, { method: 'POST' });
  },

  // ShopEase Live Integration API
  getShopEaseHealth: () => request('/shopease/health'),
  getShopEaseMetrics: () => request('/shopease/metrics'),
  getShopEaseLogs: (limit = 50, severity = null, service = null) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    if (severity) params.append('severity', severity);
    if (service) params.append('service', service);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/shopease/logs${qs}`);
  },
  getShopEaseServices: () => request('/shopease/services'),
  getShopEaseSnapshot: () => request('/shopease/snapshot'),
  getShopEaseFaults: () => request('/shopease/faults'),
  injectShopEaseFault: (scenario, params = {}) =>
    request('/shopease/faults/inject', {
      method: 'POST',
      body: JSON.stringify({ scenario, params })
    }),
  disableShopEaseFault: (scenario) =>
    request('/shopease/faults/disable', {
      method: 'POST',
      body: JSON.stringify({ scenario })
    }),
  resetShopEaseFaults: () =>
    request('/shopease/faults/reset', { method: 'POST' }),
  detectAndInvestigateShopEase: () =>
    request('/shopease/detect-and-investigate', { method: 'POST' }),
  listShopEaseIncidents: (status) => {
    const qs = status ? `?status=${status}` : '';
    return request(`/shopease/incidents${qs}`);
  },

  // Autonomous Background Monitoring Controls
  getMonitoringStatus: () => request('/shopease/monitoring/status'),
  startMonitoring: () => request('/shopease/monitoring/start', { method: 'POST' }),
  stopMonitoring: () => request('/shopease/monitoring/stop', { method: 'POST' }),
  pollMonitoringNow: () => request('/shopease/monitoring/poll-now', { method: 'POST' }),

  // Customer Workload Controls
  getWorkloadStatus: () => request('/shopease/workload/status'),
  startWorkload: (params = { concurrency: 35, ramp_seconds: 6.0, delay_sec: 0.04 }) =>
    request('/shopease/workload/start', {
      method: 'POST',
      body: JSON.stringify(params)
    }),
  stopWorkload: () => request('/shopease/workload/stop', { method: 'POST' }),
  getShopEaseRemediationStatus: () => request('/shopease/remediation/status'),

  // Remediation
  getAllowlist: () => request('/remediation/allowlist'),
  approveRemediation: (id, data) =>
    request(`/remediation/approve/${id}`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  executeRemediation: (id, simulateVerificationFailure = false) =>
    request(`/remediation/execute/${id}`, {
      method: 'POST',
      body: JSON.stringify({
        incident_id: id,
        simulate_verification_failure: simulateVerificationFailure
      })
    }),

  // Retrieval
  compareRetrieval: (payload) =>
    request('/retrieval/compare', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getHistoricalCases: () => request('/retrieval/historical-cases'),

  // Experiments
  runExperiment: (payload = { threshold: 0.55, top_k: 3 }) =>
    request('/experiments/run', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  getLastExperimentResults: () => request('/experiments/last-results'),

  // Dataset
  importKaggleSample: () =>
    request('/dataset/import-kaggle-sample', { method: 'POST' }),
  uploadDataset: (formData) =>
    request('/dataset/upload', {
      method: 'POST',
      body: formData
    }),
  getDatasetStats: () => request('/dataset/stats'),
  previewDataset: () => request('/dataset/preview')
};
