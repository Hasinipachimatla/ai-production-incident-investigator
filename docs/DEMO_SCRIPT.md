# Live Demonstration Walkthrough Script (Faculty & Reviewer Guide)

This script provides step-by-step instructions for demonstrating the **AI Production Incident Investigator** during a college project review. It is structured to be easy to follow and explain in under 10 minutes.

---

## Prerequisites: Launch Servers

In two separate PowerShell terminal windows:

### Terminal 1: Backend
```powershell
cd "c:\Users\Satish P\Desktop\Ai-Incident-Investigator\AI-Incident-Investigator"
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```
*Backend runs on `http://127.0.0.1:8000` with Swagger docs at `http://127.0.0.1:8000/docs`.*

### Terminal 2: Frontend
```powershell
cd "c:\Users\Satish P\Desktop\Ai-Incident-Investigator\AI-Incident-Investigator"
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```
*Frontend runs on `http://localhost:5173`.*

Open your browser to `http://localhost:5173`.

---

## Part 1: Primary Demonstration Mode A — Realistic Workload-Driven Autonomous Incident Resolution (No Synthetic Faults)

**Faculty Talking Point:**
> *"In production systems, operational degradation rarely begins with someone injecting a predefined chaos script. It arises naturally from real customer traffic saturating resource bottlenecks. Here, we demonstrate autonomous incident discovery, investigation, approval, and resolution under pure customer traffic without injecting any synthetic fault."*

### Automated Execution (Exact Script)
In a PowerShell window:
```powershell
python .\scripts\test_workload_driven_incident.py
```

### Live UI Walkthrough:
1. Open the React Dashboard at `http://localhost:5173`.
2. Notice the top target switcher is set to `🛒 Live ShopEase (:5000)` and the autonomous background daemon shows `● Monitoring Active (3s)`.
3. In the **⚡ Customer Workload Generator** card:
   - Click **▶ Start Customer Traffic (35 Users)**.
   - Watch the traffic badge pulse green in the header: `130+ RPS`.
4. Within 4 to 8 seconds:
   - Natural PostgreSQL connection pool contention develops under search queries.
   - P99 latency rises above the 500ms SLO threshold.
   - The autonomous background daemon observes $\ge 2$ consecutive anomalous poll cycles.
   - A bright red autonomous incident alert banner appears at the top:
     `🚨 ACTIVE AUTONOMOUS INCIDENT [INC-...] | PostgreSQL Database contention / Catalog Latency | Action: rate_limit_throttle`
5. Click **Investigate & Review Incident →**:
   - Evidence-based RCA explains the bottleneck and presents historical precedents matched at $\theta=0.55$.
   - SRE Human Approval Gate is enforced: Click **✓ Authorize & Approve Fix**.
6. Watch Real Operational Remediation in ShopEase:
   - Investigator applies `POST /api/remediation/apply`.
   - In ShopEase, dynamic concurrency bounding activates: excess searches are shed to read cache snapshots.
   - While customer traffic continues at 130+ RPS, latency collapses from >800ms down to <30ms!
   - Independent multi-SLO verifier probes ShopEase and confirms recovery.
   - Incident transitions to **`RESOLVED`** and banner turns green!

---

## Part 2: Demonstration Mode B — Controlled Microservice Fault Injection Lab (5 Scenarios)

Walk through the 7-step guided workflow:

### Step 1 & 2: Select & Inject Controlled Fault
1. In the fault selector, select **Database Connection Pool Exhaustion** (`checkout-service`).
2. Point out the expected symptoms (Pool usage 100%, HTTP error rate spike).
3. Click **⚡ Inject Fault Scenario**.
4. Observe the immediate telemetry reaction:
   - Top status turns red: `SYSTEM ANOMALY`.
   - KPI strip shows DB Pool spiking to `100.0%` and Error Rate jumping to `38.5%`.
5. Click **Proceed to Evidence Scan →**.

### Step 3: Scan Telemetry & Correlate Evidence
1. Review the breached KPI metrics snapshot.
2. Click **🔍 Scan Telemetry & Run RCA Engine**.
3. Point out that the system detected the anomaly, correlated log lines, and created an active incident record (`INC-xxxx`).

### Step 4 & 5: AI Diagnosis & Adaptive Historical Precedents
1. **RCA Diagnosis View**:
   - Culprit Service: `checkout-service`.
   - Confidence Score: ~88% with confidence breakdown.
   - Corroborating signals: Connection timeout exceptions and pool exhaustion metrics.
2. Click **Inspect Historical Matches →**:
   - Point out that the engine matched `INC-HIST-001` with high similarity (~88%).
   - Highlight the **matched token badges** and **service affinity bonus (+15%)**.
   - Explain: *"Adaptive retrieval only matched this case because its similarity exceeded θ = 0.55. It did NOT force irrelevant cases."*
3. Click **Proceed to Human Approval Gate →**.

### Step 6: Human Approval Gate
1. Show the proposed allowlisted action: `restart_connection_pool`.
2. Explain the safety boundary: *"The backend enforces a strict allowlist. Arbitrary shell commands or unrestricted code are rejected."*
3. Leave operator name as `Incident-Commander-Alice` and click **✓ Authorize & Approve Fix**.
4. The incident status transitions to `APPROVED`.
5. Click **Proceed to Execution & Verification →**.

### Step 7: Execution & Multi-SLO Recovery Verification
1. Click **⚡ Execute Remediation & Independently Verify Recovery**.
2. Watch the live transition:
   - Status changes to `REMEDIATING` (pool recycling).
   - Then to `VERIFYING` (fresh telemetry sampling).
   - Evaluates 5 independent SLO gates: Error Rate < 2%, P99 Latency < 500ms, DB Pool < 80%, Circuit Breaker Closed, Cache Hit > 80%, and Service Fault Cleared.
   - Result confirms: **`PASSED`**.
   - Status transitions to **`RESOLVED`**.
   - Top health badge returns to green: **`SYSTEM HEALTH NOMINAL`**!

---

## Part 3: Demonstrating the Safe Retry & Escalation Loop

1. Return to **Step 1** by clicking **← Test Another Scenario**.
2. Select **Downstream Payment Gateway Latency Spike**.
3. Click **⚡ Inject Fault Scenario**, then click **Proceed to Evidence Scan →**.
4. Click **🔍 Scan Telemetry & Run RCA Engine**.
5. Proceed to **Step 6** and click **✓ Authorize & Approve Fix**.
6. In **Step 7**, check the box: **🧪 Simulate Ineffective Fix (Demonstrate Safe Retry Loop)**.
7. Click **⚡ Execute Remediation & Independently Verify Recovery**.
8. Observe:
   - Verification returns **`FAILED`** because telemetry remained breached.
   - The incident is **not closed**.
   - Status transitions to **`RETRYING (1/3)`**.
   - The system triggers re-investigation, refreshes evidence, and returns to human approval!
   - (If 3 failed attempts occur, it safely transitions to `FAILED_ESCALATED` to alert human commanders).

---

## Part 4: Research Contribution 1 — Adaptive Retrieval Workbench

1. Click the **🔬 Adaptive Retrieval (Research Gap 1)** tab.
2. Under Preset Benchmark Scenarios, select:
   - **1. PostgreSQL Connection Exhaustion (1 True Match)**:
     - Click **⚡ Run Side-by-Side Retrieval Comparison**.
     - Observe:
       - **Baseline Fixed Top-K (K=3)** forces 2 irrelevant cases ($FP=2$, Precision $33\%$).
       - **Adaptive Threshold (θ=0.55)** returns only the 1 true match ($FP=0$, Precision $100\%$).
   - **4. Novel Quantum Processor Crash (0 True Matches - Novel)**:
     - Click **⚡ Run Side-by-Side Retrieval Comparison**.
     - Observe:
       - Baseline Top-K returns 3 completely irrelevant cases ($P=0\%$).
       - Adaptive retrieval returns **0 cases**, correctly identifying a novel failure mode!
       - Explain to reviewers: *"Returning 0 matches prevents prompt pollution. It shields downstream RCA from hallucinating similarities."*

---

## Part 5: Empirical Benchmark Experiments & Sensitivity Sweep

1. Click the **📊 Evaluation Experiments** tab.
2. Review the macro KPI cards:
   - **Mean Precision**: **93.3%** vs **33.3%** (+60.0% improvement).
   - **Mean F1 Score**: **0.889** vs **0.473** (+0.416 improvement).
   - **Irrelevant Noise Reduction**: **100.0%** (30 noise cases eliminated).
   - **Mean Recall**: **86.7%** (parity maintained).
3. Expand the **Threshold Sensitivity Sweep Table**:
   - Point out that $\theta=0.55$ achieves peak F1 (0.889) and zero false positives ($FP=0$), proving that it is the optimal operating point.
4. Show the 15-query breakdown table mapping query IDs to ground-truth IDs.

---

## Part 6: Dataset Ingestion & Kaggle Pipeline

1. Click the **📁 Datasets & Kaggle Pipeline** tab.
2. Show the inspected Kaggle candidates (Candidate 1, 2, 3) and explain the authentication boundary.
3. Click **📥 Ingest Kaggle AIOps Sample Cases**.
4. Observe the repository count increase from 12 to 20 incident cases.
5. Review the updated category, service, and source statistics cards and the schema preview table.

---

## Part 7: Viva / Oral Defense Questions (Research Guide & FAQ)

At the bottom of the **🏠 Overview & Guide** page, expand the **🎓 Research Guide & Frequently Asked Questions** accordion. It is organized into 6 collapsible categories with oral defense answers:

1. **Research Contributions**: Explains Gap 1 (retrieval noise suppression) and Gap 2 (closed-loop multi-SLO verification).
2. **Retrieval & Evaluation**: Explains composite scoring $S(q, c)$, empty ground truth $|GT|=0$ convention ($P=1.0, R=1.0$ for zero retrieval), and the $\theta=0.55$ threshold trade-offs.
3. **Root Cause Analysis**: Explains evidence streams (logs, metric breaches, historical matches), confidence calculation, and contradictory evidence.
4. **Remediation & Safety**: Explains the 6 allowlisted actions, server-side validation, human authorization gate, and independent 5-SLO verification with bounded retries.
5. **Datasets & Architecture**: Clarifies the 12 curated seed cases vs. 20 post-import cases, Kaggle sample schema mapping, and FastAPI simulation testbed.
6. **Limitations & Academic Disclosures**: Transparently discloses deterministic algorithms (no generative LLM hallucinations), in-memory simulation testbed, and scope boundaries.


