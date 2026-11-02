# AI-Based Production Incident Investigator with Adaptive Root Cause Analysis and Closed-Loop Resolution

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_19_Vite-61DAFB.svg)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-65_Passed-10B981.svg)](https://pytest.org)
[![ShopEase](https://img.shields.io/badge/ShopEase-15_Passed-10B981.svg)](file:///c:/Users/Satish%20P/Desktop/ShopEase-Ecommerce)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_17-336791.svg)](https://postgresql.org)
[![Monitoring](https://img.shields.io/badge/Autonomous_Daemon-Continuous_3s-blue.svg)](#autonomous-background-monitoring)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A research platform investigating automated software production incident investigation, intelligent historical incident retrieval, and safe closed-loop automated resolution across both an internal microservice simulator and a live full-stack Indian lifestyle e-commerce application (**ShopEase E-Commerce**).

---

## 🛍️ Live Integration: ShopEase E-Commerce Testbed

The investigator connects in real-time to **ShopEase** (`http://localhost:5000`), a production-grade Node.js Express 5 + PostgreSQL 17 marketplace with 36 seeded Indian lifestyle products:
- **Real Operational Telemetry**: Live HTTP error rates, P95/P99 moving latencies, PostgreSQL connection pool queues, Redis cache hit/miss ratios, and circuit breaker trip metrics.
- **5 Controlled Fault Scenarios**:
  1. `db_exhaustion`: PostgreSQL Connection Pool Exhaustion (`postgresql-database`).
  2. `high_latency`: High API Latency Cascade (`catalog-service`).
  3. `service_error_spike`: Checkout 500 Internal Server Error Spike (`order-service`).
  4. `cache_failure`: Cache Invalidation Outage & Cold Miss Storm (`cache-service`).
  5. `circuit_breaker_trip`: Downstream RPC Circuit Breaker Trip (`inventory-service`).
- **Strict Anti-Leakage Guarantee**: Test harness logs (`service: "fault-manager"`) are strictly filtered from telemetry; RCA operates exclusively on observable symptoms.
- **Independent Verification**: Post-remediation status is confirmed through fresh active API probes to `/api/products` and `/api/categories`.
- **Autonomous Background Monitoring Daemon**: Continuous polling loop running every 3.0s in FastAPI independent of browser presence. Uses consecutive streak tracking ($\ge 2$) to reject transient jitter and automatically create incidents with evidence in `AWAITING_APPROVAL` status upon sustained anomalies.
- **Target Switcher**: The frontend dashboard allows one-click switching between `Live ShopEase (:5000)` and `Internal Simulator`.

---

## 🔬 Core Research Contributions

### Research Gap 1: Adaptive Historical Incident Retrieval
Conventional automated incident investigation systems employ a **Fixed Top-K baseline** (typically $K=3$ or $K=5$) to retrieve past post-mortems. When an active failure matches only one prior incident, or is completely novel, fixed Top-K forces irrelevant cases into the context window, contaminating root-cause reasoning and inducing AI hallucinations.

**Our Proposed Solution**: A **Relevance-Threshold Adaptive Retrieval** mechanism ($\theta = 0.55$) combining TF-IDF sublinear vectorization, n-gram token overlap scoring, and dynamic score drop-off truncation. 
- Evaluated across 15 benchmark incident queries against identical historical cases.
- **+60.00% Absolute Precision Improvement** (93.33% vs 33.33%).
- **100.0% Reduction in Irrelevant Noise Cases** (0 irrelevant cases vs 30 forced by Top-K=3).
- **Zero Hallucination on Novel Faults**: Safely returns 0 cases for unprecedented incidents.

### Research Gap 2: Controlled Closed-Loop Remediation
Autonomous resolution cannot operate as an unconstrained open loop. This platform implements a safe, end-to-end closed loop:
1. **Anomaly Detection**: Scans continuous telemetry metrics against SLO thresholds.
2. **Evidence-Based RCA**: Gathers metric breaches and error logs; live RCA inputs are strictly separated from ground-truth evaluation labels.
3. **Safe Allowlisted Actions**: Proposes reversible mitigations strictly validated against a safe allowlist (`restart_connection_pool`, `rate_limit_throttle`, `flush_and_warm_cache`, `rollback_config_flag`, `reset_circuit_breaker`, `scale_worker_replicas`).
4. **Human-in-the-Loop Approval Gate**: Requires explicit operator validation before execution.
5. **Post-Fix SLO Recovery Verification**: Verifies actual system telemetry recovery against healthy baselines before closing incidents.
6. **Bounded Retry & Safe Escalation**: If verification fails, keeps the incident open, triggers re-investigation, and retries safely up to a limit (3 attempts) before escalating to human on-call engineers.

---

## 🚀 Quickstart: Exact Windows PowerShell Commands

### 1. Install Backend & Frontend Dependencies
```powershell
# In project root:
cd backend
python -m pip install -r requirements.txt

cd ..\frontend
npm install
cd ..
```

### 2. Start the FastAPI Backend
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```
*API runs at `http://127.0.0.1:8000` (Swagger interactive docs at `http://127.0.0.1:8000/docs`).*

### 3. Start the React Frontend Dashboard
*In a second terminal window:*
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```
*Web dashboard opens at `http://localhost:5173`.*

### 4. Run Automated Test Suite (65 Backend + 15 ShopEase Tests Passed)
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_tests.ps1
```

### 5. Mode A (Primary Demonstration): Realistic Workload-Driven Autonomous Incident Resolution
*Demonstrates that operational incident detection, RCA, historical retrieval, human approval, closed-loop remediation, and multi-SLO recovery operate completely naturally under realistic customer traffic WITHOUT synthetic fault injection:*
```powershell
python .\scripts\test_workload_driven_incident.py
```

### 6. Mode B: Live ShopEase 5-Scenario Controlled Fault Injection Lab
*Validates the closed-loop remediation lifecycle across all 5 standard distributed microservice failure scenarios:*
```powershell
python .\scripts\validate_live_shopease_scenarios.py
```

### 7. Execute Comparative Benchmark Experiments
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_experiments.ps1
```

---

## 📊 Summary of Actual Computed Experiment Results

| Metric | Baseline (Fixed Top-K=3) | Proposed (Adaptive $\theta=0.55$) | Delta |
|---|---|---|---|
| **Mean Precision** | **33.33%** | **93.33%** | **+60.00%** |
| **Mean Recall** | **86.67%** | **86.67%** | **Parity** |
| **Mean F1 Score** | **0.4733** | **0.8889** | **+0.4156** |
| **Total Cases Retrieved** | 45 | 12 | -33 noise cases |
| **Irrelevant Cases ($FP$)** | **30** | **0** | **-100.0%** |
| **Avg. Irrelevant / Query** | 2.00 | 0.00 | -2.00 noise / query |

---

## 🎓 Academic Review Defense (12 Questions Answered)

1. **Why use ShopEase when the research is not about e-commerce?**  
   ShopEase serves as a representative microservice topology (checkout, payment, catalog, inventory, recommendations) exhibiting standard distributed failure modes (database pool exhaustion, cascading thread starvation, cache storms, circuit breaker trips). The research contributions—adaptive incident retrieval and closed-loop allowlisted remediation—are domain-agnostic and apply to any cloud-native service mesh.

2. **What exactly are the two research gaps?**  
   - *Gap 1 (Retrieval Noise)*: Fixed Top-K retrieval forces irrelevant historical incidents into LLM/RCA contexts whenever a problem has fewer than $K$ true matches or is novel, inducing hallucinations.
   - *Gap 2 (Unsafe Remediation)*: Open-loop autonomous fixing risks arbitrary command execution and lacks independent post-execution recovery verification with bounded retries.

3. **What is the proposed contribution beyond existing RCA approaches?**  
   We provide a deterministic, zero-paid-API system integrating relevance-threshold retrieval ($\theta=0.55$) with backend allowlist validation, human-in-the-loop approval, independent multi-metric SLO verification, and safe re-investigation state transitions.

4. **How does adaptive retrieval differ from fixed Top-K?**  
   Fixed Top-K returns exactly $K$ documents regardless of score. Adaptive retrieval enforces a minimum relevance threshold ($\theta=0.55$) and dynamic score drop-off truncation ($\Delta \le 0.35$), returning 0 cases for novel incidents.

5. **How are precision, recall, and F1 calculated?**  
   $TP = |R \cap G|$, $FP = |R \setminus G|$, $FN = |G \setminus R|$. When $|R|=0$ and $|G|=0$, $P=1.0, R=1.0, F_1=1.0$ (perfect noise suppression). When $|R|=0$ and $|G|>0$, $P=0.0, R=0.0, F_1=0.0$. Otherwise, $P = TP/(TP+FP)$, $R = TP/(TP+FN)$, $F_1 = 2PR/(P+R)$.

6. **How do you prevent ground-truth leakage?**  
   Ground-truth labels are completely isolated within `eval_labeled_dataset.json`. The live RCA engine (`rca_engine.py`) and live telemetry service have no access to ground-truth labels.

7. **How does the system verify recovery?**  
   `recovery_verifier.py` checks actual telemetry against 5 SLO thresholds (error rate $\le 2\%$, P99 latency $\le 500$ms, DB pool $\le 80\%$, circuit breaker closed, cache hit $\ge 60\%$) and confirms target service fault clearance rather than superficial HTTP 200 responses.

8. **What happens after an ineffective fix?**  
   If an approved action does not resolve the active fault, the fault remains active and verification fails. The incident remains OPEN in `AWAITING_APPROVAL`, increments `retry_count`, re-investigates with fresh evidence, and proposes an alternative corrective action.

9. **Which actions are truly executed and which are simulated?**  
   All 6 actions mutate the controlled in-memory microservice testbed (`fault_simulator.py`), resetting connection pools, clearing queues, and updating cache states. We explicitly disclose that actions are executed against this controlled simulator rather than bare-metal production hosts.

10. **What dataset was actually used?**  
    A 15-query labeled benchmark dataset (`data/eval_labeled_dataset.json`) and 12-case repository (`data/historical_incidents.json`), supplemented by a verified Kaggle AIOps Failure Detection dataset schema sample (`data/sample_kaggle_aiops.csv`).

11. **What are the limitations of the experiments?**  
    Evaluated on a 15-query curated benchmark; large enterprises possess thousands of cases. Uses deterministic TF-IDF + token overlap rather than dense neural embeddings to ensure zero paid API dependencies and 100% local reproducibility.

12. **What evidence supports the reported improvement?**  
    Independently verified by automated test suites (35 tests passing) and freshly generated benchmark outputs (`data/last_experiment_results.csv` and `.json`), demonstrating +60.00% precision improvement and 100.0% reduction in irrelevant noise.

---

## 📁 Repository Structure

```
AI-Incident-Investigator/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (faults, incidents, retrieval, remediation, experiments, dataset)
│   │   ├── core/            # Config, SQLite setup, remediation allowlist
│   │   ├── models/          # SQLAlchemy ORM models (Incident, HistoricalCase, AuditLog)
│   │   ├── schemas/         # Pydantic v2 validation models
│   │   ├── services/        # Fault simulator, RCA engine, retrieval engine, verifier, experiment runner
│   │   └── main.py          # FastAPI application & startup seeder
│   ├── tests/               # 35 automated tests (unit, API, closed-loop, dataset pipeline)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # FaultControlPanel, IncidentsView, RetrievalWorkbench, ExperimentWorkbench, DatasetManager
│   │   ├── api.js           # REST API client
│   │   ├── App.jsx          # Main application coordinating state & tabs
│   │   └── index.css        # Dark mode glassmorphism design system
│   ├── package.json
│   └── vite.config.js       # Vite dev server with /api proxy
├── data/
│   ├── historical_incidents.json   # 12 initial curated benchmark incident cases
│   ├── eval_labeled_dataset.json   # 15 evaluation queries with separate ground truth labels
│   ├── sample_kaggle_aiops.csv     # Verified Kaggle AIOps dataset schema sample
│   ├── last_experiment_results.json# Persisted computed benchmark JSON results
│   └── last_experiment_results.csv # Machine-readable CSV breakdown & aggregate results
├── docs/
│   ├── REQUIREMENTS_TRACEABILITY.md # Traceability matrix for all project requirements
│   ├── ARCHITECTURE.md      # Detailed system architecture, Mermaid diagrams, API specs
│   ├── EXPERIMENTS.md       # Benchmark protocol, mathematical metric formulations
│   ├── RESULTS.md           # Actual computed experimental numbers & query breakdown
│   ├── DATASET_GUIDE.md     # Kaggle candidates inspection, download & import guide
│   └── DEMO_SCRIPT.md       # Step-by-step evaluation & live demonstration script
├── scripts/
│   ├── run_backend.ps1      # PowerShell backend launcher
│   ├── run_frontend.ps1     # PowerShell frontend launcher
│   ├── run_tests.ps1        # PowerShell automated test runner
│   ├── run_experiments.ps1  # PowerShell experiment execution script
│   └── evaluate_thresholds.py # Threshold sensitivity sweep analysis script
└── README.md
```

---

## 📚 Documentation Index

- **[Requirements Traceability Matrix](docs/REQUIREMENTS_TRACEABILITY.md)**: Every requirement mapped to files, tests, and statuses.
- **[System Architecture](docs/ARCHITECTURE.md)**: System design, Mermaid diagrams, module interactions, and security gates.
- **[Experimental Methodology](docs/EXPERIMENTS.md)**: Metric formulations, hypothesis testing, and benchmark query taxonomy.
- **[Computed Research Results](docs/RESULTS.md)**: Complete 15-query breakdown table, macro performance metrics, and discussion.
- **[Kaggle Dataset Guide](docs/DATASET_GUIDE.md)**: Kaggle candidate inspection, CLI setup, and schema mapping pipeline.
- **[Live Demonstration Script](docs/DEMO_SCRIPT.md)**: Step-by-step walkthrough script for demonstrating both research gaps.

