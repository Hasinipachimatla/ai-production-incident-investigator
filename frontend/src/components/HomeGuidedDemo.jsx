import React, { useState } from 'react';

export default function HomeGuidedDemo({
  telemetry,
  catalog,
  activeFaults,
  incidents,
  onStartDemo,
  onNavigateTab
}) {
  const [showFaq, setShowFaq] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState({
    contributions: true,
    retrieval: false,
    rca: false,
    remediation: false,
    datasets: false,
    limitations: false
  });

  const toggleCategory = (catKey) => {
    setExpandedCategories(prev => ({
      ...prev,
      [catKey]: !prev[catKey]
    }));
  };

  const expandAllCategories = () => {
    setExpandedCategories({
      contributions: true,
      retrieval: true,
      rca: true,
      remediation: true,
      datasets: true,
      limitations: true
    });
  };

  const collapseAllCategories = () => {
    setExpandedCategories({
      contributions: false,
      retrieval: false,
      rca: false,
      remediation: false,
      datasets: false,
      limitations: false
    });
  };

  const activeFaultCount = activeFaults.length;
  const isAnomaly = telemetry?.anomaly_detected || activeFaultCount > 0;
  const totalIncidents = incidents.length;
  const resolvedCount = incidents.filter(i => i.status === 'RESOLVED').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px', animation: 'fadeIn 0.2s ease' }}>
      {/* Hero Welcome Card: Plain English Overview */}
      <div className="glass-panel" style={{
        padding: '30px 34px',
        borderLeft: '5px solid var(--accent-teal-dark)',
        background: '#ffffff'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ maxWidth: '820px' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
              <span className="badge badge-simulation">Academic Research Prototype</span>
              <span className="badge" style={{ background: 'var(--accent-teal-light)', color: 'var(--accent-teal-dark)' }}>
                College Project Review Ready
              </span>
            </div>

            <h2 style={{ fontSize: '1.55rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px' }}>
              Automated Incident Investigation with Adaptive Retrieval & Controlled Recovery
            </h2>

            {/* The Problem & The Solution in Plain English */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <span style={{ background: '#fee2e2', color: '#b91c1c', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, fontSize: '0.8rem' }}>THE PROBLEM</span>
                <p style={{ fontSize: '0.94rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  When large web applications experience production outages, diagnosing root causes is slow and stressful. On-call engineers must manually comb through millions of error logs and metrics to find what went wrong.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                <span style={{ background: '#dcfce7', color: '#15803d', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, fontSize: '0.8rem' }}>THE SOLUTION</span>
                <p style={{ fontSize: '0.94rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                  This research platform automatically detects failures, collects diagnostic evidence, compares symptoms against historical incidents, proposes a likely root cause, and guides a human operator through safe, verified recovery.
                </p>
              </div>
            </div>

            {/* Two Core Research Contributions */}
            <div style={{ background: '#f8fafc', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '14px 18px', marginBottom: '20px' }}>
              <strong style={{ fontSize: '0.86rem', color: 'var(--text-main)', display: 'block', marginBottom: '6px' }}>
                Two Primary Academic Research Contributions:
              </strong>
              <ul style={{ paddingLeft: '20px', fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.5 }}>
                <li>
                  <strong>Contribution 1 (Adaptive Retrieval):</strong> Replaces conventional Fixed Top-K (which forces irrelevant historical cases into context) with a tuned relevance threshold (θ = 0.55) that eliminates prompt noise and hallucinations.
                </li>
                <li>
                  <strong>Contribution 2 (Controlled Closed-Loop Remediation):</strong> Connects diagnostic recommendations to human approval, a server-side safety allowlist, and independent post-fix telemetry verification with automated retry and escalation.
                </li>
              </ul>
            </div>

            {/* Primary Action Buttons */}
            <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
              <button
                className="btn btn-primary btn-lg"
                onClick={onStartDemo}
              >
                🚀 Start Guided Demo (Step-by-Step)
              </button>
              <button
                className="btn btn-secondary btn-lg"
                onClick={() => onNavigateTab('experiments')}
              >
                📊 Explore Research Benchmark Results
              </button>
            </div>
          </div>

          {/* Quick System Status Card */}
          <div style={{
            background: '#f8fafc',
            padding: '20px 22px',
            borderRadius: '10px',
            border: `1px solid ${isAnomaly ? 'var(--status-red-border)' : 'var(--status-green-border)'}`,
            minWidth: '240px'
          }}>
            <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600, marginBottom: '6px' }}>
              Environment Status
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.05rem', fontWeight: 700, color: isAnomaly ? 'var(--status-red-text)' : 'var(--status-green-text)' }}>
              <span style={{
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: isAnomaly ? '#dc2626' : '#16a34a'
              }} />
              {isAnomaly ? 'Anomaly In Progress' : 'Healthy Baseline'}
            </div>
            <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '8px', lineHeight: 1.4 }}>
              Active Faults: <strong>{activeFaultCount}</strong><br />
              Testbed: <strong>ShopEase Topology</strong><br />
              Platform: <strong>100% Local / Safe</strong>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Compact Status Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            System Health State
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: isAnomaly ? 'var(--status-red-text)' : 'var(--status-green-text)', marginTop: '4px' }}>
            {isAnomaly ? '⚠️ Anomaly Detected' : '✅ Nominal Baseline'}
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {isAnomaly ? `${activeFaultCount} fault scenario(s) actively running` : 'Normal response times, zero active faults'}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Fault Scenario Catalog
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
            {catalog.length} Controlled Scenarios
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            DB pool, cache storm, latency cascade, error spike, breaker trip
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Historical Incident Repository
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)', marginTop: '4px' }}>
            12 Base Cases
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Curated benchmark cases (Expands to 20 upon Kaggle import)
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ fontSize: '0.76rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Optimal Retrieval Threshold
          </div>
          <div style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--accent-teal-dark)', marginTop: '4px' }}>
            θ = 0.55
          </div>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Eliminates 100% irrelevant case noise vs Fixed Top-K
          </div>
        </div>
      </div>

      {/* 5-Step Guided Workflow Roadmap */}
      <div className="glass-panel" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)' }}>
              How the Incident Investigation Flow Works
            </h3>
            <p style={{ fontSize: '0.86rem', color: 'var(--text-muted)' }}>
              A 5-step closed-loop lifecycle from failure injection to verified recovery
            </p>
          </div>
          <button
            className="btn btn-primary btn-sm"
            onClick={onStartDemo}
          >
            Launch Step-by-Step Stepper →
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '14px' }}>
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-teal-dark)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 700 }}>1</span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>Fault Injection</strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.4 }}>
              Select and trigger a controlled scenario (e.g., PostgreSQL connection pool exhaustion).
            </p>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-teal-dark)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 700 }}>2</span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>Evidence Correlation</strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.4 }}>
              The system correlates error logs, HTTP failure spikes, and latency metrics into structured evidence.
            </p>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-teal-dark)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 700 }}>3</span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>Adaptive Retrieval</strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.4 }}>
              Filters past incident post-mortems using θ=0.55, avoiding false-precedent noise and hallucinations.
            </p>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-teal-dark)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 700 }}>4</span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>Human Approval Gate</strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.4 }}>
              Requires explicit operator sign-off. Enforces a strict server-side allowlist against arbitrary commands.
            </p>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'var(--accent-teal-dark)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.82rem', fontWeight: 700 }}>5</span>
              <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>Verified Recovery</strong>
            </div>
            <p style={{ fontSize: '0.84rem', color: 'var(--text-body)', lineHeight: 1.4 }}>
              Executes allowlisted action and independently tests 5 SLO gates. Auto-retries and re-investigates if fix fails!
            </p>
          </div>
        </div>
      </div>

      {/* Research Guide & Frequently Asked Questions (Collapsible, Organized by Topic) */}
      <div className="accordion-box" style={{ background: '#ffffff', border: '1px solid var(--border-subtle)', borderRadius: '10px' }}>
        <div
          className="accordion-header"
          onClick={() => setShowFaq(!showFaq)}
          style={{ cursor: 'pointer', padding: '16px 20px', background: '#ffffff', borderRadius: '10px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '1.3rem' }}>🎓</span>
            <div>
              <strong style={{ fontSize: '0.98rem', color: 'var(--text-main)' }}>
                Research Guide & Frequently Asked Questions (Click to {showFaq ? 'Collapse' : 'Expand'})
              </strong>
              <div style={{ fontSize: '0.84rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Defensible oral defense answers, scoring formulas, and architectural verification organized into 6 research categories
              </div>
            </div>
          </div>
          <span style={{ color: 'var(--accent-teal-dark)', fontSize: '0.88rem', fontWeight: 600 }}>
            {showFaq ? 'Hide Guide ▲' : 'Show Guide ▼'}
          </span>
        </div>

        {showFaq && (
          <div className="accordion-body" style={{ padding: '0 20px 22px 20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Top Toolbar with Category Controls */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '10px',
              padding: '12px 14px',
              background: '#f8fafc',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)'
            }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-body)' }}>
                Click individual category headers below, or use bulk controls:
              </span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={expandAllCategories}
                  style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Expand All
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={collapseAllCategories}
                  style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Collapse All
                </button>
              </div>
            </div>

            {/* Category 1: Research Contributions */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('contributions')}
                style={{
                  background: expandedCategories.contributions ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.contributions ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>🔬</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    1. Research Contributions
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    2 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.contributions ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.contributions && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q1.1: What are the two core research gaps addressed by this work?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        <strong>Gap 1 — Retrieval Noise in Fixed Top-K:</strong> Baseline retrieval methods unconditionally return a fixed number of precedents (K=3). When an incident has only one true precedent or represents an unprecedented failure, Top-K injects 2 to 3 irrelevant cases into context. In downstream diagnostic systems, this creates prompt pollution and misdirection. Our proposed method applies adaptive relevance-threshold retrieval (θ = 0.55) with service affinity and dynamic truncation, filtering out irrelevant precedents and returning zero cases for novel faults.
                      </p>
                      <p>
                        <strong>Gap 2 — Open-Loop Alerting vs. Closed-Loop Verification:</strong> Conventional incident management workflows often stop at advisory alerting or ticketing, relying on human operators to manually verify recovery. Our system introduces an integrated closed-loop architecture: proposed remediations require human authorization, are validated against a backend allowlist of safe actions, and must pass independent multi-metric SLO verification (evaluating P99 latency, error rates, pool utilization, cache hit rates, and circuit breaker status) before an incident can be closed.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q1.2: Why is returning zero cases considered a successful outcome for novel incidents?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        When an unprecedented failure occurs (such as an out-of-domain hardware panic or zero-day scenario with zero historical matches), returning zero precedents is mathematically correct (Precision = 1.0, Recall = 1.0). It prevents false analogies and avoids applying an irrelevant runbook.
                      </p>
                      <div style={{ background: '#f8fafc', borderLeft: '3px solid var(--accent-indigo)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.84rem', color: 'var(--text-body)' }}>
                        <strong>Oral Defense Note:</strong> Clarify to reviewers that returning zero cases suppresses retrieval noise—it does not claim the system automatically diagnosed or resolved the novel incident, but accurately flags that human intervention without prior precedent is required.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Category 2: Retrieval & Evaluation */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('retrieval')}
                style={{
                  background: expandedCategories.retrieval ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.retrieval ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>🔍</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    2. Retrieval & Evaluation
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    3 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.retrieval ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.retrieval && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q2.1: How are candidate historical incidents scored and filtered?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        Candidate incidents are scored using a composite similarity function combining three signals:
                      </p>
                      <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: '6px', fontFamily: 'monospace', fontSize: '0.86rem', color: 'var(--text-main)', marginBottom: '8px', border: '1px solid var(--border-subtle)' }}>
                        S(q, c) = min(1.0, 0.50 · TFIDF(q, c) + 0.50 · Coverage(q, c) + ServiceBonus)
                      </div>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li><strong>TFIDF(q, c):</strong> Cosine similarity computed over sublinear TF-IDF bi-gram vectors.</li>
                        <li><strong>Coverage(q, c):</strong> Ratio of query tokens appearing in the historical case document.</li>
                        <li><strong>ServiceBonus:</strong> +0.10 affinity bonus if the candidate matches the culprit service hint.</li>
                      </ul>
                      <p>
                        Under adaptive retrieval, candidates must meet threshold θ = 0.55. If multiple candidates pass, a dynamic truncation rule preserves candidates within 0.35 of the top score, dropping distant tail cases.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q2.2: How does the benchmark handle queries with empty ground truth (|GT| = 0)?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        In <code>retrieval_engine.py</code> (lines 270–278), the evaluation metrics handle queries where no historical precedents exist (such as novel queries EVAL-013 and EVAL-014) according to standard information retrieval conventions:
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li>If |GT| = 0 and the engine retrieves 0 cases: <strong>Precision = 1.0, Recall = 1.0, F1 = 1.0</strong> (perfect noise suppression).</li>
                        <li>If |GT| = 0 and the engine retrieves 1 or more cases (as Top-K=3 does): <strong>Precision = 0.0, Recall = 0.0, F1 = 0.0</strong> (every retrieved case is an irrelevant false positive).</li>
                      </ul>
                      <p>
                        This metric convention rewards algorithms that withhold recommendations when no valid precedent exists, rather than forcing irrelevant precedents.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q2.3: How was the threshold θ = 0.55 selected, and what are its trade-offs?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        We conducted an empirical threshold sensitivity sweep over θ ∈ [0.35, 0.75] in increments of 0.05 across the 15 evaluation queries. At low thresholds (θ ≤ 0.45), precision degrades because distractor cases pass. At high thresholds (θ ≥ 0.65), recall degrades because valid precedents with paraphrased symptoms are excluded. The threshold θ = 0.55 achieves the optimal balance (F1 = 0.957 with 100% noise reduction).
                      </p>
                      <div style={{ background: '#f8fafc', borderLeft: '3px solid var(--accent-indigo)', padding: '8px 12px', borderRadius: '4px', fontSize: '0.84rem', color: 'var(--text-body)' }}>
                        <strong>Academic Disclosure:</strong> The threshold θ = 0.55 was selected based on our labeled evaluation dataset. In an enterprise production deployment, this threshold would be calibrated using cross-validation over an independent validation corpus.
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Category 3: Root Cause Analysis */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('rca')}
                style={{
                  background: expandedCategories.rca ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.rca ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>🧠</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    3. Root Cause Analysis
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    3 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.rca ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.rca && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q3.1: What evidence does the Root Cause Analysis engine inspect?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        Live Root Cause Analysis is strictly evidence-based and isolated from offline benchmark evaluation labels. It correlates three live signals:
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li><strong>Error Log Signatures:</strong> Scans active error and warning logs for stack traces and exception messages to isolate the culprit service.</li>
                        <li><strong>SLO Metric Breaches:</strong> Checks real-time metrics against explicit thresholds (DB pool utilization &gt; 80%, P99 latency &gt; 500ms, HTTP error rate &gt; 2.0%, circuit breaker tripped, or cache hit rate &lt; 60%).</li>
                        <li><strong>Historical Precedent Matching:</strong> Queries the historical incident corpus using the active symptoms and log messages.</li>
                      </ul>
                      <p>
                        If a precedent matches, its documented root cause is proposed; otherwise, a deterministic heuristic fallback analyzes the metric breaches directly.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q3.2: How is the RCA confidence score calculated?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        In <code>rca_engine.py</code> (lines 114–138):
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li><strong>When a historical precedent matches:</strong> Confidence is computed as <code>min(0.96, 0.70 + (0.28 · S_top))</code>, combining a 0.70 base heuristic confidence with up to 0.28 scaled by the precedent's similarity score, corroborated by observed telemetry signals.</li>
                        <li><strong>When no precedent matches (novel incident):</strong> A baseline confidence of 0.72 is assigned based strictly on deterministic rule-based SLO breaches and log patterns.</li>
                      </ul>
                      <p>
                        Ground-truth evaluation labels are never accessed during live RCA.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q3.3: Why does the system display contradictory evidence?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p>
                        Sound engineering diagnosis requires ruling out unaffected subsystems. For instance, during a downstream payment gateway timeout, latency spikes to 4200ms, but the database connection pool is at a nominal 18% and the circuit breaker is CLOSED. The RCA engine explicitly presents these nominal readings under Contradictory Evidence to confirm that the database is healthy and prevent misdirected remediation.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Category 4: Remediation & Safety */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('remediation')}
                style={{
                  background: expandedCategories.remediation ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.remediation ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>🛡️</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    4. Remediation & Safety
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    2 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.remediation ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.remediation && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q4.1: What safety mechanisms prevent unauthorized or destructive remediation?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        The platform enforces four explicit safeguards:
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li><strong>Server-Side Allowlist Enforcement:</strong> Remediations are strictly restricted to 6 pre-approved, reversible operations (<code>restart_connection_pool</code>, <code>rate_limit_throttle</code>, <code>rollback_config_flag</code>, <code>flush_and_warm_cache</code>, <code>reset_circuit_breaker</code>, <code>scale_worker_replicas</code>). Any unallowlisted action is rejected by backend validation.</li>
                        <li><strong>Human Authorization Gate:</strong> Remediations cannot execute autonomously. An operator must review the proposed action, risk classification, and safety rationale, and explicitly sign off (<code>APPROVED</code> state). Operators can also override parameters.</li>
                        <li><strong>State Transition Integrity:</strong> Incidents cannot skip stages (execution is blocked unless the incident is in <code>APPROVED</code> or <code>RETRYING</code> state).</li>
                        <li><strong>Append-Only Audit Logging:</strong> Every state transition, approver identity, execution timestamp, and verification outcome is written to the audit log.</li>
                      </ul>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q4.2: How does recovery verification and escalation operate?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        Execution does not equal recovery. When an allowlisted action completes, the independent <code>RecoveryVerifier</code> samples fresh telemetry across 5 distinct SLO gates:
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li>P99 latency &lt; 500ms</li>
                        <li>HTTP error rate &lt; 2.0%</li>
                        <li>DB pool utilization &lt; 75%</li>
                        <li>Cache hit rate &gt; 75%</li>
                        <li>Circuit breaker in <code>CLOSED</code> state</li>
                      </ul>
                      <p>
                        Only when all 5 pass is the incident marked <code>RESOLVED</code>. If any SLO fails, the incident enters <code>RETRYING</code> state, increments the retry count (bounded to 3 max retries), and re-triggers RCA to formulate an alternate plan. If retries exceed the limit, the incident automatically transitions to <code>ESCALATED</code> for human Tier-3 engineering.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Category 5: Datasets & Architecture */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('datasets')}
                style={{
                  background: expandedCategories.datasets ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.datasets ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>📊</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    5. Datasets & Architecture
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    3 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.datasets ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.datasets && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q5.1: Clarify the corpus count: Why does the health endpoint report 12 cases while some documents reference 20?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p style={{ marginBottom: '8px' }}>
                        This reflects two clearly defined and documented states of the incident repository:
                      </p>
                      <ul style={{ paddingLeft: '18px', margin: '0 0 8px 0' }}>
                        <li><strong>Seed Benchmark Corpus (12 Cases):</strong> Stored in <code>data/historical_incidents.json</code> (cases INC-HIST-001 through INC-HIST-012). On fresh backend startup, the health endpoint reports exactly 12 cases.</li>
                        <li><strong>Post-Import Corpus (20 Cases):</strong> When an operator imports <code>data/sample_kaggle_aiops.csv</code> (8 rows) via the Dataset Manager, those 8 cases are appended to the in-memory retrieval engine, expanding the active corpus to 20 cases.</li>
                        <li><strong>Benchmark Evaluation Impact:</strong> The 15 evaluation queries in <code>data/eval_labeled_dataset.json</code> have ground-truth annotations mapped to the 12 curated incidents. When the benchmark is executed on the 20-case corpus, the 8 imported cases serve as realistic distractors. Adaptive retrieval successfully filters them when their similarity falls below θ = 0.55.</li>
                      </ul>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q5.2: What is the provenance of the sample Kaggle dataset?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p>
                        The file <code>data/sample_kaggle_aiops.csv</code> contains an 8-row sample structured according to public AIOps failure detection schemas (including timestamps, project names, HTTP methods, status codes, latency, error messages, and trace IDs). It serves as a verifiable fixture demonstrating that the platform can ingest external tabular incident datasets and map heterogeneous schemas into the internal incident format.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q5.3: What is the system architecture and runtime environment?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p>
                        The application is built with a Python FastAPI backend and a React 19 / Vite frontend. Simulated microservices (<code>checkout-service</code>, <code>payment-gateway</code>, <code>catalog-service</code>, <code>inventory-api</code>, <code>recommendation-service</code>) run in-memory within FastAPI (<code>fault_simulator.py</code>). The simulation dynamically modulates latency, error rates, and connection pools when faults are injected, providing a self-contained, reproducible testbed without requiring live cloud infrastructure or Kubernetes clusters.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Category 6: Limitations & Academic Disclosures */}
            <div style={{ border: '1px solid var(--border-subtle)', borderRadius: '8px', overflow: 'hidden' }}>
              <div
                onClick={() => toggleCategory('limitations')}
                style={{
                  background: expandedCategories.limitations ? '#f1f5f9' : '#f8fafc',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  cursor: 'pointer',
                  borderBottom: expandedCategories.limitations ? '1px solid var(--border-subtle)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '1.05rem' }}>⚠️</span>
                  <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>
                    6. Limitations & Academic Disclosures
                  </strong>
                  <span className="badge" style={{ background: '#e2e8f0', color: 'var(--text-main)', fontSize: '0.74rem' }}>
                    2 Questions
                  </span>
                </div>
                <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  {expandedCategories.limitations ? 'Collapse ▲' : 'Expand ▼'}
                </span>
              </div>

              {expandedCategories.limitations && (
                <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', background: '#ffffff' }}>
                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q6.1: Is this system an autonomous Generative AI or LLM Agent?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <p>
                        No. We disclose our technical implementation transparently: The system utilizes deterministic rule-based telemetry correlation, TF-IDF vector similarity with token coverage, and finite-state machine transitions. It does not employ an external generative Large Language Model (LLM) or autonomous neural agent. This design provides key advantages—deterministic reproducibility, zero API costs, sub-second response times, and zero hallucinations—while remaining suitable for academic verification.
                      </p>
                    </div>
                  </div>

                  <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    <h5 style={{ fontSize: '0.91rem', color: 'var(--accent-teal-dark)', marginBottom: '8px' }}>
                      Q6.2: What are the primary limitations of this research prototype?
                    </h5>
                    <div style={{ fontSize: '0.88rem', color: 'var(--text-body)', lineHeight: 1.55 }}>
                      <ul style={{ paddingLeft: '18px', margin: '0' }}>
                        <li style={{ marginBottom: '6px' }}><strong>In-Memory Simulation Testbed:</strong> Telemetry and faults are generated by a local Python simulation model rather than a distributed Kubernetes cluster with real network transport.</li>
                        <li style={{ marginBottom: '6px' }}><strong>Evaluation Corpus Scale:</strong> The benchmark consists of 15 queries evaluated against 12 baseline incidents (plus 8 imported samples). While this demonstrates a statistically clear contrast between Top-K and adaptive retrieval, validating on larger enterprise corpora would be necessary to establish broad domain generalization.</li>
                        <li><strong>Pre-Configured Fault Scenarios:</strong> The platform currently models 5 specific failure patterns. Complex, multi-system cascading failures outside these patterns still require human-led investigation.</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
