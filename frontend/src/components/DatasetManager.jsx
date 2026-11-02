import React, { useState } from 'react';

export default function DatasetManager({
  datasetStats,
  onImportSampleKaggle,
  onUploadDataset,
  isImporting,
  previewData
}) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [showProvenanceInfo, setShowProvenanceInfo] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadStatus('Uploading and parsing dataset...');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      const res = await onUploadDataset(formData);
      setUploadStatus(`Success: Imported ${res.imported_count} cases (${res.format_detected})`);
      setSelectedFile(null);
    } catch (err) {
      setUploadStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px', animation: 'fadeIn 0.2s ease' }}>
      {/* Educational Banner: Dataset Provenance */}
      <div className="glass-panel" style={{ padding: '24px 28px', borderLeft: '5px solid var(--status-green-text)', background: '#ffffff' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
          <span className="badge badge-simulation">Research Integrity & Provenance</span>
          <span className="badge" style={{ background: 'var(--status-green-bg)', color: 'var(--status-green-text)', border: '1px solid var(--status-green-border)' }}>
            AIOps Schema Importer
          </span>
        </div>
        <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
          Dataset Ingestion Pipeline & Provenance Disclosures
        </h3>
        <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
          Our platform isolates evaluation labels from operational inputs and provides an automated schema ingestion pipeline 
          for standard AIOps observability logs. To maintain strict academic integrity, we candidly disclose all dataset sources, 
          provenance boundaries, and authentication requirements.
        </p>
      </div>

      {/* Kaggle Candidates Inspection Cards */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>Inspected Public Kaggle Candidates</h4>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setShowProvenanceInfo(!showProvenanceInfo)}
          >
            {showProvenanceInfo ? 'Hide Auth Policy ▲' : 'Kaggle Auth Policy ▼'}
          </button>
        </div>

        {showProvenanceInfo && (
          <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '16px 20px', marginBottom: '16px', fontSize: '0.86rem', color: 'var(--text-body)' }}>
            ℹ️ <strong>Kaggle Download Gate:</strong> Kaggle requires user authentication cookies or API tokens (<code>~/.kaggle/kaggle.json</code>). Unauthenticated automated curl downloads return HTTP 404 / Login redirect. We provide <code>data/sample_kaggle_aiops.csv</code> as a pre-verified schema sample matching Candidate 1.
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
          <div className="glass-panel" style={{ padding: '18px 20px', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>Candidate 1: AIOps Failure Detection</strong>
              <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)' }}>Target Schema</span>
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginBottom: '10px', lineHeight: 1.4 }}>
              Structured telemetry with error_message, root_cause, and resolution_action. Matches our schema 1-to-1.
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              License: MIT | URL: <code>expertshubham/aiops-log-monitoring-and-failure-detection-dataset</code>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px 20px', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>Candidate 2: Software Observability</strong>
              <span className="badge" style={{ background: '#f1f5f9', color: '#475569' }}>Inspected</span>
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginBottom: '10px', lineHeight: 1.4 }}>
              Multi-language microservice failure traces (NullPointer, timeout, out-of-memory).
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              License: Apache 2.0 | URL: <code>sohamphdresearch/software-observability-dataset</code>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '18px 20px', background: '#ffffff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <strong style={{ fontSize: '0.95rem', color: 'var(--text-main)' }}>Candidate 3: Logging & Monitoring</strong>
              <span className="badge" style={{ background: '#f1f5f9', color: '#475569' }}>Inspected</span>
            </div>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginBottom: '10px', lineHeight: 1.4 }}>
              Operational performance metrics timeseries and general system log streams.
            </p>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              License: MIT | URL: <code>sagniksen3025/logging-and-monitoring-data</code>
            </div>
          </div>
        </div>
      </div>

      {/* Dataset Actions: 1-Click Kaggle Ingestion & Custom Upload */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '18px' }}>
        {/* Built-in Sample Ingestion */}
        <div className="glass-panel" style={{ padding: '22px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', background: '#ffffff' }}>
          <div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
              1-Click Verified Kaggle Dataset Ingestion
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-body)', marginBottom: '18px', lineHeight: 1.4 }}>
              Ingest the verified Kaggle AIOps dataset sample (matching Candidate 1) directly into the active retrieval corpus. Increases repository from 12 base cases to 20 total cases.
            </p>
          </div>

          <button
            className="btn btn-primary"
            onClick={onImportSampleKaggle}
            disabled={isImporting}
          >
            {isImporting ? 'Ingesting Cases...' : '📥 Ingest Kaggle AIOps Sample Cases'}
          </button>
        </div>

        {/* Custom Upload */}
        <div className="glass-panel" style={{ padding: '22px', background: '#ffffff' }}>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Upload Custom CSV / JSON
          </h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-body)', marginBottom: '14px', lineHeight: 1.4 }}>
            Upload an external dataset file. The automatic column mapper detects incident schemas automatically.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <input
              type="file"
              accept=".csv,.json"
              onChange={handleFileChange}
              style={{ background: '#f8fafc', border: '1px solid var(--border-card)', padding: '8px 12px', fontSize: '0.86rem' }}
            />

            <button
              className="btn btn-secondary btn-sm"
              onClick={handleUpload}
              disabled={!selectedFile}
            >
              Parse & Ingest File
            </button>

            {uploadStatus && (
              <div style={{ fontSize: '0.84rem', color: uploadStatus.startsWith('Error') ? 'var(--status-red-text)' : 'var(--status-green-text)', marginTop: '4px', fontWeight: 500 }}>
                {uploadStatus}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Active Repository Statistics */}
      {datasetStats && (
        <div className="glass-panel" style={{ padding: '22px', background: '#ffffff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)' }}>Active Incident Repository Statistics</h4>
            <span className="badge badge-resolved">
              {datasetStats.total_cases} Total Incident Cases Loaded
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
            <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '8px' }}>
                By Failure Category
              </div>
              {Object.entries(datasetStats.categories || {}).map(([cat, count]) => (
                <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.84rem' }}>
                  <span style={{ color: 'var(--text-body)' }}>{cat}</span>
                  <strong style={{ color: 'var(--text-main)' }}>{count}</strong>
                </div>
              ))}
            </div>

            <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '8px' }}>
                By Microservice
              </div>
              {Object.entries(datasetStats.services || {}).map(([svc, count]) => (
                <div key={svc} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.84rem' }}>
                  <span style={{ color: 'var(--accent-teal-dark)', fontWeight: 500 }}>{svc}</span>
                  <strong style={{ color: 'var(--text-main)' }}>{count}</strong>
                </div>
              ))}
            </div>

            <div style={{ background: '#f8fafc', padding: '14px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '8px' }}>
                By Origin Source
              </div>
              {Object.entries(datasetStats.sources || {}).map(([src, count]) => (
                <div key={src} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.84rem' }}>
                  <span style={{ color: 'var(--accent-indigo)', fontWeight: 500 }}>{src}</span>
                  <strong style={{ color: 'var(--text-main)' }}>{count}</strong>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Schema Preview Table */}
      {previewData && (
        <div className="glass-panel" style={{ padding: '22px', overflowX: 'auto', background: '#ffffff' }}>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
            Schema Preview ({previewData.filename})
          </h4>
          <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginBottom: '14px' }}>
            Sample rows parsed and ingested into the vector retrieval engine:
          </p>

          <table className="data-table" style={{ fontSize: '0.82rem' }}>
            <thead>
              <tr>
                {previewData.headers?.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewData.sample_rows?.map((row, i) => (
                <tr key={i}>
                  {previewData.headers?.map((h) => (
                    <td key={h} style={{ maxWidth: '180px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {row[h]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
