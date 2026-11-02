import React, { useState } from 'react';

const PRESET_QUERIES = [
  {
    label: "1. PostgreSQL Pool Exhaustion (1 True Match)",
    text: "PostgreSQL connection pool exhausted in checkout service with queue pool timeout errors and remaining connection slots reserved",
    service: "checkout-service",
    gt: ["INC-HIST-001"],
    notes: "Baseline Top-K forces 2 irrelevant cases. Adaptive returns only the 1 true match (100% precision)."
  },
  {
    label: "2. Payment Gateway Read Timeout (1 True Match)",
    text: "Slow response from payment gateway downstream, read timeout exceptions and blocked worker threads causing 504 gateway timeout",
    service: "payment-gateway",
    gt: ["INC-HIST-002"],
    notes: "Demonstrates service affinity matching and latency token correlation."
  },
  {
    label: "3. Redis Cache Key Invalidation Storm (1 True Match)",
    text: "Redis cache stampede with synchronized key expiration causing database CPU saturation and severe cache hit ratio drop",
    service: "catalog-service",
    gt: ["INC-HIST-003"],
    notes: "Demonstrates cache stampede keyword matching."
  },
  {
    label: "4. Novel Quantum Processor Crash (0 True Matches - Novel)",
    text: "Novel hardware optical quantum tensor processor cooled with liquid helium kernel panic during matrix compute",
    service: "inference-node",
    gt: [],
    notes: "Novel out-of-domain incident with 0 true matches. Adaptive returns 0 cases, avoiding hallucinated precedents."
  }
];

export default function RetrievalWorkbench({ onCompare, comparisonResult, isComparing }) {
  const [queryText, setQueryText] = useState(PRESET_QUERIES[0].text);
  const [serviceHint, setServiceHint] = useState(PRESET_QUERIES[0].service);
  const [threshold, setThreshold] = useState(0.55);
  const [topK, setTopK] = useState(3);
  const [activePreset, setActivePreset] = useState(0);
  const [showMathDetails, setShowMathDetails] = useState(false);

  const handleSelectPreset = (idx) => {
    setActivePreset(idx);
    const p = PRESET_QUERIES[idx];
    setQueryText(p.text);
    setServiceHint(p.service);
  };

  const handleRun = () => {
    const selectedPreset = activePreset !== null ? PRESET_QUERIES[activePreset] : null;
    onCompare({
      query_text: queryText,
      service: serviceHint,
      top_k: Number(topK),
      threshold: Number(threshold),
      ground_truth_case_ids: selectedPreset ? selectedPreset.gt : null
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px', animation: 'fadeIn 0.2s ease' }}>
      {/* Educational Banner: Research Gap 1 */}
      <div className="glass-panel" style={{ padding: '24px 28px', borderLeft: '5px solid var(--accent-teal-dark)', background: '#ffffff' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
          <span className="badge badge-simulation">Research Contribution 1</span>
          <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)' }}>
            Retrieval Precision vs Prompt Noise
          </span>
        </div>
        <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
          Adaptive Historical Incident Retrieval Workbench
        </h3>
        <p style={{ fontSize: '0.92rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
          <strong>The Research Question:</strong> In automated incident diagnosis, conventional systems use 
          <strong> Fixed Top-K (K=3)</strong>, always retrieving 3 cases even when an incident has only 1 true precedent 
          or represents an unprecedented novel failure. This forces 2 to 3 irrelevant cases into context. 
          Our proposed <strong>Adaptive Relevance-Threshold (θ = 0.55)</strong> filters out sub-threshold candidates, 
          eliminating false positives and prompt noise.
        </p>
      </div>

      {/* Query Formulation & Controls */}
      <div className="glass-panel" style={{ padding: '24px 28px', background: '#ffffff' }}>
        <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px' }}>
          Step 1: Select or Formulate an Incident Query
        </h4>

        {/* Preset Buttons */}
        <div style={{ marginBottom: '18px' }}>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '8px' }}>
            Preset Benchmark Scenarios:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
            {PRESET_QUERIES.map((p, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectPreset(idx)}
                style={{
                  background: activePreset === idx ? 'var(--accent-teal-light)' : '#f8fafc',
                  border: `1.5px solid ${activePreset === idx ? 'var(--accent-teal-dark)' : 'var(--border-subtle)'}`,
                  padding: '12px 14px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <strong style={{ fontSize: '0.88rem', color: activePreset === idx ? 'var(--accent-teal-dark)' : 'var(--text-main)', display: 'block', marginBottom: '4px' }}>
                  {p.label}
                </strong>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.3 }}>{p.notes}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Query Text Area */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '0.84rem', color: 'var(--text-main)', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
            Incident Query Text (Symptoms & Log Message Signatures):
          </label>
          <textarea
            rows={3}
            value={queryText}
            onChange={(e) => {
              setQueryText(e.target.value);
              setActivePreset(null);
            }}
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>

        {/* Sliders & Parameters */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <label style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
              Service Context Hint
            </label>
            <input
              type="text"
              value={serviceHint}
              onChange={(e) => setServiceHint(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Adaptive Threshold (θ)</span>
              <strong style={{ color: 'var(--accent-teal-dark)' }}>{threshold.toFixed(2)}</strong>
            </div>
            <input
              type="range"
              min="0.30"
              max="0.80"
              step="0.05"
              value={threshold}
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              style={{ width: '100%' }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Evaluated optimal point: θ = 0.55</span>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '4px' }}>
              <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>Baseline Fixed Top-K</span>
              <strong style={{ color: 'var(--accent-indigo)' }}>K = {topK}</strong>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              step="1"
              value={topK}
              onChange={(e) => setTopK(parseInt(e.target.value))}
              style={{ width: '100%' }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Standard baseline: K = 3</span>
          </div>
        </div>

        {/* Action Button */}
        <button
          className="btn btn-primary btn-lg"
          onClick={handleRun}
          disabled={isComparing}
        >
          {isComparing ? 'Querying Backend Engine...' : '⚡ Run Side-by-Side Retrieval Comparison'}
        </button>
      </div>

      {/* Comparison Results */}
      {comparisonResult && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {/* Analysis Badge & Explanation */}
          <div className="glass-panel" style={{ padding: '18px 22px', background: 'var(--accent-teal-light)', border: '1px solid #99f6e4' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <strong style={{ fontSize: '0.94rem', color: 'var(--accent-teal-dark)' }}>
                Live API Analysis Output
              </strong>
              <span className="badge" style={{ background: '#ffffff', color: 'var(--accent-teal-dark)', border: '1px solid #99f6e4' }}>
                Dynamic REST Response
              </span>
            </div>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
              {comparisonResult.analysis}
            </p>
          </div>

          {/* Metric Glossary */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '10px' }}>
            <div style={{ background: '#ffffff', padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.84rem' }}>
              <strong style={{ color: 'var(--text-main)' }}>Precision:</strong> % of retrieved cases that are truly relevant (Target: 100%, avoid noise).
            </div>
            <div style={{ background: '#ffffff', padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.84rem' }}>
              <strong style={{ color: 'var(--text-main)' }}>Recall:</strong> % of true historical precedents that were successfully found.
            </div>
            <div style={{ background: '#ffffff', padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.84rem' }}>
              <strong style={{ color: 'var(--text-main)' }}>Noise Reduction:</strong> Irrelevant historical cases filtered out before reaching prompt.
            </div>
          </div>

          {/* Side-by-Side Comparison Columns */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '20px' }}>
            {/* Left: Baseline Fixed Top-K */}
            <div className="glass-panel" style={{ padding: '22px', borderTop: '4px solid var(--accent-indigo)', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>Baseline: Fixed Top-K (K = {comparisonResult.fixed_top_k.k_applied})</h4>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Always retrieves K candidates unconditionally</span>
                </div>
                <span className="badge badge-awaiting">Static K</span>
              </div>

              {/* KPI Strip */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '16px', textAlign: 'center' }}>
                <div className="kpi-chip">
                  <span className="label">Retrieved</span>
                  <span className="value">{comparisonResult.fixed_top_k.retrieved_count}</span>
                </div>
                <div className="kpi-chip">
                  <span className="label">Irrelevant</span>
                  <span className="value" style={{ color: comparisonResult.fixed_top_k.irrelevant_count > 0 ? 'var(--status-red-text)' : 'inherit' }}>
                    {comparisonResult.fixed_top_k.irrelevant_count ?? 'N/A'}
                  </span>
                </div>
                <div className="kpi-chip">
                  <span className="label">Precision</span>
                  <span className="value">
                    {comparisonResult.fixed_top_k.precision !== null ? `${(comparisonResult.fixed_top_k.precision * 100).toFixed(0)}%` : 'N/A'}
                  </span>
                </div>
                <div className="kpi-chip">
                  <span className="label">F1 Score</span>
                  <span className="value">
                    {comparisonResult.fixed_top_k.f1_score !== null ? comparisonResult.fixed_top_k.f1_score.toFixed(2) : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Candidates */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {comparisonResult.fixed_top_k.candidates.map((c, i) => (
                  <div
                    key={c.id}
                    style={{
                      background: c.is_irrelevant ? 'var(--status-red-bg)' : '#f8fafc',
                      border: `1px solid ${c.is_irrelevant ? 'var(--status-red-border)' : 'var(--border-subtle)'}`,
                      padding: '14px',
                      borderRadius: '8px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>#{i + 1} {c.id}</strong>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        {c.is_irrelevant && (
                          <span className="badge badge-escalated" style={{ fontSize: '0.7rem' }}>
                            Irrelevant Noise
                          </span>
                        )}
                        <span style={{ color: 'var(--accent-teal-dark)', fontWeight: 700, fontSize: '0.86rem' }}>
                          Score: {(c.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginBottom: '3px' }}>{c.title}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Historical Fix: {c.recommended_remediation}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Adaptive Threshold */}
            <div className="glass-panel" style={{ padding: '22px', borderTop: '4px solid var(--accent-teal-dark)', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-main)' }}>Proposed: Adaptive (θ ≥ {comparisonResult.adaptive.threshold_applied})</h4>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Filters low-confidence noise candidates</span>
                </div>
                <span className="badge badge-resolved">Dynamic Filtering</span>
              </div>

              {/* KPI Strip */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '16px', textAlign: 'center' }}>
                <div className="kpi-chip">
                  <span className="label">Retrieved</span>
                  <span className="value" style={{ color: 'var(--accent-teal-dark)' }}>{comparisonResult.adaptive.retrieved_count}</span>
                </div>
                <div className="kpi-chip">
                  <span className="label">Irrelevant</span>
                  <span className="value" style={{ color: 'var(--status-green-text)' }}>
                    {comparisonResult.adaptive.irrelevant_count ?? 0}
                  </span>
                </div>
                <div className="kpi-chip">
                  <span className="label">Precision</span>
                  <span className="value" style={{ color: 'var(--status-green-text)' }}>
                    {comparisonResult.adaptive.precision !== null ? `${(comparisonResult.adaptive.precision * 100).toFixed(0)}%` : 'N/A'}
                  </span>
                </div>
                <div className="kpi-chip">
                  <span className="label">F1 Score</span>
                  <span className="value" style={{ color: 'var(--status-green-text)' }}>
                    {comparisonResult.adaptive.f1_score !== null ? comparisonResult.adaptive.f1_score.toFixed(2) : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Candidates */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {comparisonResult.adaptive.candidates.length === 0 ? (
                  <div style={{
                    background: '#f8fafc',
                    border: '1.5px dashed var(--border-card)',
                    padding: '24px',
                    borderRadius: '8px',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '1.6rem', marginBottom: '4px' }}>🛡️</div>
                    <strong style={{ fontSize: '0.94rem', color: 'var(--text-main)' }}>Zero Candidates Admitted (Novel Mode)</strong>
                    <p style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: 1.4 }}>
                      All candidates fell below threshold θ = {comparisonResult.adaptive.threshold_applied}. 
                      Recognized as an unprecedented novel failure, shielding downstream RCA from hallucination.
                    </p>
                  </div>
                ) : (
                  comparisonResult.adaptive.candidates.map((c, i) => (
                    <div
                      key={c.id}
                      style={{
                        background: '#ffffff',
                        border: '1.5px solid #99f6e4',
                        padding: '14px',
                        borderRadius: '8px',
                        boxShadow: 'var(--shadow-sm)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                        <strong style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>#{i + 1} {c.id}</strong>
                        <span style={{ color: 'var(--accent-teal-dark)', fontWeight: 700, fontSize: '0.86rem' }}>
                          Score: {(c.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.86rem', color: 'var(--text-body)', marginBottom: '3px' }}>{c.title}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Historical Fix: {c.recommended_remediation}</div>
                      {c.matching_evidence && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px', fontSize: '0.76rem' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Matched Tokens:</span>
                          {c.matching_evidence.matched_tokens?.map((t, idx) => (
                            <span key={idx} style={{ background: '#f1f5f9', color: '#1e293b', padding: '1px 6px', borderRadius: '4px', border: '1px solid #cbd5e1' }}>{t}</span>
                          ))}
                          {c.matching_evidence.service_match && (
                            <span style={{ background: 'var(--status-green-bg)', color: 'var(--status-green-text)', padding: '1px 7px', borderRadius: '4px', border: '1px solid var(--status-green-border)', fontWeight: 600 }}>
                              Service Match (+15%)
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Research Details & Math Formulation Accordion */}
          <div className="accordion-box">
            <div className="accordion-header" onClick={() => setShowMathDetails(!showMathDetails)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>📐</span>
                <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                  Mathematical Scoring Formulation & Empty Ground-Truth Convention (Click to {showMathDetails ? 'Collapse' : 'Expand'})
                </strong>
              </div>
              <span style={{ fontSize: '0.84rem', color: 'var(--accent-teal-dark)', fontWeight: 600 }}>
                {showMathDetails ? 'Hide Formulas ▲' : 'Show Formulas ▼'}
              </span>
            </div>
            {showMathDetails && (
              <div className="accordion-body" style={{ background: '#ffffff', fontSize: '0.86rem', color: 'var(--text-body)', lineHeight: 1.6 }}>
                <p style={{ marginBottom: '8px' }}>
                  <strong>Relevance Scoring Function:</strong>
                  <br />
                  <code>S(q, c) = min(1.0, 0.5 · TFIDF(q, c) + 0.5 · TokenCoverage(q, c) + ServiceBonus)</code>
                  <br />
                  where <code>ServiceBonus = 0.15</code> if candidate service matches query service hint, else <code>0.0</code>.
                </p>
                <p style={{ marginBottom: '8px' }}>
                  <strong>Relative Drop-Off Truncation:</strong> In addition to threshold θ = 0.55, candidates whose similarity score drops by &gt; 25% relative to the top candidate are truncated: <code>S(q, c) ≥ 0.75 · max(S)</code>.
                </p>
                <p>
                  <strong>Empty Ground-Truth Evaluation Convention:</strong> For novel queries where ground-truth |GT| = 0, returning 0 candidates represents a true negative (evaluated as Precision = 1.0, Recall = 1.0). Returning any candidates is evaluated as Precision = 0.0, Recall = 0.0.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
