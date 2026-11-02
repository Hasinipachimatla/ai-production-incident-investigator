# End-to-End System Demonstration & Reviewer Walkthrough Guide
## AI Production Incident Investigator + ShopEase E-Commerce Integration

This document provides exact, reproducible Windows PowerShell commands and step-by-step instructions for demonstrating the **AI Production Incident Investigator** running closed-loop investigation and remediation against the **live ShopEase Indian lifestyle e-commerce application**.

---

## 1. Architecture & Port Layout

| System | Role | Technology | Port | Primary URL |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 17** | Production Database | PostgreSQL Service | `5432` | `localhost:5432/shopease_db` |
| **ShopEase E-Commerce** | Target Application | Node.js Express 5 | `5000` | `http://localhost:5000` |
| **AI Investigator Backend**| AI Engine & Closed-Loop Controller | FastAPI (Python 3.11) | `8000` | `http://127.0.0.1:8000` |
| **Investigator UI** | SRE Commander Dashboard | React 19 + Vite | `5173` | `http://localhost:5173` |

---

## 2. Prerequisites & Server Launch Instructions

Open **three** separate Windows PowerShell terminal windows:

### Terminal 1: Start ShopEase Application
```powershell
# Verify PostgreSQL is running
Get-Service -Name *postgres*

# Start ShopEase E-Commerce Marketplace
cd "C:\Users\Satish P\Desktop\ShopEase-Ecommerce"
npm start
```
*Expected Output:*
```
🛍️ ShopEase server is running at http://localhost:5000
🛠️ System Reliability Lab available at http://localhost:5000#reliability-lab
📊 Observability Metrics: http://localhost:5000/api/observability/metrics
```

### Terminal 2: Start AI Incident Investigator Backend
```powershell
cd "C:\Users\Satish P\Desktop\Ai-Incident-Investigator\AI-Incident-Investigator"
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```
*Expected Output:*
```
INFO:     Started server process
INFO:     Waiting for application startup.
[Startup] Loaded 12 historical incident cases into Retrieval Engine.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 3: Start AI Investigator Web Frontend
```powershell
cd "C:\Users\Satish P\Desktop\Ai-Incident-Investigator\AI-Incident-Investigator"
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```
*Expected Output:*
```
VITE v8.3.4  ready in 280 ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

## 3. Verify Health & Connectivity Endpoints

In an additional PowerShell terminal or browser:

```powershell
# 1. ShopEase Direct Health Check
curl http://localhost:5000/api/health

# 2. Investigator Direct Health Check
curl http://127.0.0.1:8000/api/health

# 3. Investigator-to-ShopEase Adapter Connectivity Check
curl http://127.0.0.1:8000/api/shopease/health

# 4. Live Telemetry Snapshot
curl http://127.0.0.1:8000/api/shopease/snapshot
```

All four commands return HTTP 200 with JSON verdicts confirming connected state.

---

## 4. Demonstration Mode A (Primary): Realistic Workload-Driven Autonomous Incident Resolution

In production systems, incidents do not occur because an engineer triggered a chaos script; they arise naturally when real user workload saturates operational bottlenecks. This demonstration showcases pure customer traffic driving resource contention, autonomous background detection, evidence-based RCA, human approval, real operational remediation, and recovery verification:

### CLI Execution
Run the automated acceptance suite verifying all 9 lifecycle phases:
```powershell
python .\scripts\test_workload_driven_incident.py
```

### Interactive UI Walkthrough
1. In the dashboard at `http://localhost:5173`, confirm the target switcher is set to `🛒 Live ShopEase (:5000)`.
2. Locate the **Customer Workload Generator** card in the dashboard.
3. Click **▶ Start Customer Traffic (35 Users)**:
   - 35 concurrent simulated customer sessions begin browsing, searching, and viewing products.
   - The header traffic badge pulses green, showing real-time RPS (~130+ requests/sec).
4. Within 4-6 seconds, customer search queries saturate database connection pool limits.
5. The independent background monitoring daemon detects $\ge 2$ consecutive anomalous intervals and automatically creates an incident in SQLite:
   - A bright red banner appears: `🚨 ACTIVE AUTONOMOUS INCIDENT [INC-...] | Catalog / Database Contention | Action: rate_limit_throttle`
6. Click **Investigate & Review Incident →**:
   - Evidence-based RCA explains the contention.
   - Historical precedents matched at $\theta=0.55$ are displayed.
   - SRE Human Approval Gate is enforced.
7. Click **✓ Authorize & Approve Fix**:
   - The Investigator calls `POST /api/remediation/apply` on ShopEase.
   - Real operational controls activate in ShopEase: search query concurrency is strictly bounded to 6, and excess traffic is dynamically load-shed to memory cache snapshots.
   - Post-remediation P99 latency collapses from >800ms down to <30ms while customer traffic continues!
   - Multi-SLO verifier probes ShopEase and confirms recovery.
   - Incident transitions to **`RESOLVED`**!
8. Click **⏹ Stop Traffic** to restore nominal baseline.

---

## 5. Demonstration Mode B: Controlled Microservice Fault Injection Lab (5 Scenarios)

Open your browser to: **`http://localhost:5173`**.

In the top header, verify the target switcher is set to: **`🛒 Live ShopEase (🟢)`**.

### Scenario 1: Database Connection Pool Exhaustion
1. **Context:** Exhausts the PostgreSQL connection pool (20/20 active), creating `QueuePool` timeouts.
2. In the UI (Step 1), click **Database Connection Pool Exhaustion** (`postgresql-database`).
3. Click **⚡ Trigger Fault Scenario**.
4. Observe the immediate telemetry reaction:
   - Header badge changes to: `SYSTEM ANOMALY`.
   - DB Connection Pool KPI spikes to **100.0%** (20/20 active connections).
   - Error Rate spikes due to database timeouts on `/api/categories?nocache=true`.
5. Click **Proceed to Evidence Scan →**, then click **🔍 Scan Telemetry & Correlate Evidence**.
6. **RCA Output:**
   - Culprit Service: `category-service` / `postgresql-database`.
   - Proposed Action: `restart_connection_pool`.
   - Confidence: ~72-88% corroborated by connection exhaustion logs.
   - **Anti-Leakage Guarantee:** Point out to evaluators that `fault-manager` test-harness logs are completely excluded from evidence.
7. Click **Proceed to Human Approval Gate →** and click **✓ Authorize & Approve Fix**.
8. In Step 7, click **⚡ Execute Remediation & Independently Verify Recovery**:
   - The backend releases held PostgreSQL connections.
   - Independent verification actively probes `/api/products` and `/api/categories`.
   - All 6 SLO gates confirm `PASSED`. Incident transitions to **`RESOLVED`**!

---

### Scenario 2: High API Latency Cascade
1. **Context:** Injects an artificial +2000ms delay into catalogue search routes.
2. In the UI, select **High API Latency Cascade** (`catalog-service`).
3. Click **⚡ Trigger Fault Scenario**.
4. Observe: P99 Response Time KPI spikes to **>2000 ms**.
5. Click **Scan Telemetry & Correlate Evidence**:
   - Detected breach: `p99_latency_ms breached > 500.0 ms`.
   - AI Diagnosis: `Upstream thread starvation and latency cascade identified`.
   - Proposed Allowlisted Fix: `rate_limit_throttle`.
6. Authorize and click **Execute Remediation & Verify Recovery**:
   - Delay is removed.
   - Fresh active probe measures latency dropping back to **~25 ms** (< 500ms SLO).
   - Verification confirms **`PASSED`** and incident closes as **`RESOLVED`**.

---

### Scenario 3: Checkout Order 500 Error Spike
1. **Context:** Simulates unhandled null pointer exception on order checkout transactions.
2. Select **Checkout Order 500 Error Spike** (`order-service`).
3. Click **⚡ Trigger Fault Scenario**.
4. Observe: Error Rate KPI spikes to **> 30%**.
5. Run **Scan Telemetry & Correlate Evidence**:
   - Culprit Service: `order-service`.
   - Proposed Action: `rollback_config_flag`.
6. Authorize and click **Execute Remediation & Verify Recovery**:
   - Error flag is rolled back.
   - Live checkout probing confirms successful order creation (`HTTP 201 Created`).
   - Incident transitions to **`RESOLVED`**.

---

### Scenario 4: Cache Invalidation Storm & Outage
1. **Context:** Sets cache service to `UNAVAILABLE`, forcing cold miss queries onto PostgreSQL primary.
2. Select **Cache Invalidation Outage** (`cache-service`).
3. Click **⚡ Trigger Fault Scenario**.
4. Observe: Cache Hit Ratio drops to **0.0%**.
5. Run **Scan Telemetry & Correlate Evidence**:
   - Proposed Action: `flush_and_warm_cache`.
6. Authorize and Execute Remediation:
   - Cache cluster is restored to `AVAILABLE` with cache warming.
   - Verification probes confirm cache hits and incident resolves.

---

### Scenario 5: Downstream Circuit Breaker Trip
1. **Context:** Downstream inventory failures trip the circuit breaker from `CLOSED` to `OPEN`.
2. Select **Circuit Breaker Trip (Inventory)** (`inventory-service`).
3. Click **⚡ Trigger Fault Scenario**.
4. Observe: Circuit Breaker State KPI changes to **OPEN**.
5. Run **Scan Telemetry & Correlate Evidence**:
   - Culprit: `inventory-service`.
   - Proposed Action: `reset_circuit_breaker`.
6. Authorize and Execute Remediation:
   - Circuit breaker resets to `CLOSED`.
   - Verification probes confirm fast 200 OK responses and incident resolves.

---

## 5. Demonstrating Safety Controls: Retry & Escalation Loop

1. In Step 1, select any scenario and inject the fault.
2. Progress to Step 6 and click **✓ Authorize & Approve Fix**.
3. In Step 7, check the box: **🧪 Simulate Ineffective Fix (Demonstrate Safe Retry Loop)**.
4. Click **⚡ Execute Remediation & Independently Verify Recovery**.
5. Observe:
   - The verifier detects that SLOs remain breached: **`FAILED`**.
   - Incident is **not closed**.
   - State advances to **`RETRYING`**, triggers re-investigation to find alternative mitigations, and returns to **`AWAITING_APPROVAL`**.
   - If 3 failed attempts occur, it safely transitions to **`FAILED_ESCALATED`** to hand control to a human incident commander.

---

## 6. Demonstrating Research Contribution 1: Adaptive Retrieval

Click the **🔬 Adaptive Retrieval (Research Gap 1)** tab in the top navigation:

1. **Select Preset 1 (Single True Match - PostgreSQL Exhaustion):**
   - Click **⚡ Run Side-by-Side Retrieval Comparison**.
   - **Fixed Top-K (K=3):** Returns 3 cases (1 true match + 2 completely irrelevant cases). Precision = **33.3%**.
   - **Adaptive Threshold ($\theta=0.55$):** Returns only the 1 relevant precedent case. Precision = **100.0%**. Noise cases = **0**.
2. **Select Preset 4 (Novel Incident - 0 True Matches):**
   - Click **⚡ Run Side-by-Side Retrieval Comparison**.
   - **Fixed Top-K (K=3):** Forces 3 completely irrelevant cases into context ($P=0\%$).
   - **Adaptive Threshold:** Returns **0 cases**, correctly identifying a novel failure mode and shielding downstream prompts from hallucination!

---

## 7. Running Full Automated Verification Suites

To show reviewers that 100% of the project is verified:

```powershell
# 1. Run ShopEase Reliability Test Suite (15/15 Passed)
cd "C:\Users\Satish P\Desktop\ShopEase-Ecommerce"
npm test

# 2. Run Investigator Pytest Suite (59/59 Passed)
cd "C:\Users\Satish P\Desktop\Ai-Incident-Investigator\AI-Incident-Investigator"
python -m pytest backend/tests -v

# 3. Run Live Autonomous Background Monitoring Validation Script
python scripts/test_live_automatic_monitoring.py

# 4. Run Live 5-Scenario Closed-Loop Automated Validation Script
python scripts/validate_live_shopease_scenarios.py

# 5. Run Threshold Sensitivity Sweep Script
python scripts/evaluate_thresholds.py

# 6. Run Frontend Production Build (0 Errors)
cd frontend
npm run build
```

---

## 8. Oral Defense / Viva Technical Q&A Cheat Sheet

### Q1: Why did you build an adaptive threshold rather than standard Top-K retrieval?
**Answer:** Standard Top-K unconditionally returns $K$ documents regardless of semantic distance. In production incident management, novel failures have zero precedents in historical post-mortems; forcing $K=3$ injects irrelevant context into the prompt, leading to diagnostic hallucinations. Adaptive threshold ($\theta=0.55$) filters out irrelevant cases and returns 0 documents for novel incidents, reducing irrelevant noise intrusion by 100%.

### Q2: How do you guarantee the AI doesn't know the injected fault name beforehand (Anti-Leakage)?
**Answer:** The test harness injects faults into ShopEase, but all harness logs (tagged `service: "fault-manager"`) are strictly stripped before reaching the investigator's telemetry pipeline. The RCA engine only observes genuine application side-effects (HTTP 500 error rates, P99 response time, DB pool saturation, and application stack traces). Ground-truth labels are kept isolated in evaluation datasets.

### Q3: Why is human-in-the-loop approval required? Can the system execute arbitrary shell commands?
**Answer:** No. Full autonomy in production remediation is hazardous. The system implements a strict server-side allowlist (`restart_connection_pool`, `rate_limit_throttle`, `rollback_config_flag`, `flush_and_warm_cache`, `reset_circuit_breaker`). Any arbitrary command is blocked with a security exception. Furthermore, incidents enter `AWAITING_APPROVAL` status; execution cannot proceed without cryptographic or session approval by an authorized operator.

### Q4: How does independent recovery verification prevent false-positive recoveries?
**Answer:** Many AIOps platforms declare success merely if an execution API returns HTTP 200. Our system independently waits for a stabilization window, collects fresh post-remediation metrics, and actively issues synthetic HTTP probes to `/api/products` and `/api/categories`. Only if all multi-dimensional SLO gates pass (latency < 500ms, error rate < 2%, pool < 80%, circuit breaker closed) is the incident closed as `RESOLVED`. If any SLO fails, bounded retries (up to 3) are triggered before escalating to `FAILED_ESCALATED`.

