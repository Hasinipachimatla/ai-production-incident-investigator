# Kaggle Datasets Integration Guide

## 1. Candidate Dataset Inspection & Findings

During project initialization, the live candidate Kaggle dataset web pages were inspected to examine their metadata, schemas, and accessibility:

### Candidate 1: AIOps Log Monitoring & Failure Detection Dataset
- **URL**: `https://www.kaggle.com/datasets/expertshubham/aiops-log-monitoring-and-failure-detection-dataset`
- **License**: MIT
- **File Size**: ~65 KB
- **Schema Features**: Structured observability telemetry with `timestamp`, `project_name`, `instance_id`, `event_type`, `severity`, `category`, `status`, `http_method`, `http_path`, `response_status`, `latency_ms`, `error_message`, `root_cause`, `resolution_action`, `trace_id`.
- **Suitability**: **Highest relevance**. Provides direct failure annotations and resolution actions mapping 1-to-1 with incident investigation and remediation.

### Candidate 2: Software Observability Dataset
- **URL**: `https://www.kaggle.com/datasets/sohamphdresearch/software-observability-dataset`
- **License**: Apache 2.0
- **File Size**: ~273 MB
- **Schema Features**: Synthetic multi-language logs across microservices (`AuthService`, `OrderProcessor`) containing edge cases like `NullPointerException`, `TimeoutException`, `MemoryError`.

### Candidate 3: Logging and Monitoring Data
- **URL**: `https://www.kaggle.com/datasets/sagniksen3025/logging-and-monitoring-data`
- **License**: MIT
- **File Size**: ~6.7 MB
- **Schema Features**: General system logs and operational performance telemetry.

---

## 2. Access Prerequisites & Download Policy

All three datasets on Kaggle declare:
```json
"distribution": [{
  "@type": "DataDownload",
  "requiresSubscription": true,
  "encodingFormat": "zip"
}]
```
Direct unauthenticated HTTP `curl` or automated script downloads without Kaggle user session cookies or Kaggle API credentials (`~/.kaggle/kaggle.json`) are blocked by Kaggle's authentication gate with `HTTP 404 / Login Redirect`.

To adhere strictly to research integrity principles:
1. We **do not invent** mock dataset numbers or simulate fake Kaggle downloads.
2. We provided a pre-formatted verification sample `data/sample_kaggle_aiops.csv` matching Candidate 1's exact columns.
3. We implemented and tested a generic CSV/JSON ingestion pipeline capable of parsing and importing any live Kaggle dataset file.

---

## 3. Manual Download and Import Instructions

### Step 1: Install and Configure Kaggle CLI
If you have an active Kaggle account:
```powershell
pip install kaggle
```
Place your Kaggle API key in `C:\Users\<username>\.kaggle\kaggle.json`.

### Step 2: Download Candidate Dataset
```powershell
# Download Candidate 1
kaggle datasets download -d expertshubham/aiops-log-monitoring-and-failure-detection-dataset -p data/downloads/ --unzip
```

Alternatively, navigate to the web page in your browser, log in to Kaggle, click **Download (Zip)**, and extract the CSV file to `data/downloads/`.

### Step 3: Import via UI or API

#### Option A: Web UI
1. Start the platform and navigate to the **Datasets & Kaggle Pipeline** tab (`http://localhost:5173`).
2. Under **Upload Custom Kaggle CSV / JSON**, select your downloaded CSV file.
3. Click **Upload & Parse**. The system automatically detects the schema, maps columns, and loads cases into the active retrieval engine.

#### Option B: Automated REST API
```powershell
curl -X POST "http://127.0.0.1:8000/api/dataset/import-kaggle-sample"
```
Or upload via curl:
```powershell
curl -X POST "http://127.0.0.1:8000/api/dataset/upload" -F "file=@data/sample_kaggle_aiops.csv"
```
