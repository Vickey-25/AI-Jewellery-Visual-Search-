# Lumière — AI Jewellery Visual Search: Load Testing Harness

This directory contains the production-readiness load and concurrency testing harness for the Lumière AI Visual Search backend.

## Directory Structure

```text
evaluation/load_test/
├── load_test.py
├── README.md
└── results/
    ├── load_test_results.json
    ├── load_test_results_1_worker.json
    ├── load_test_results_2_workers.json
    └── LOAD_TEST_REPORT.md
```

## How to Run Load Tests

### 1. Start the Lumière Backend Server

Start Uvicorn in production mode (without `--reload`):

**Single Worker Mode (Baseline):**
```powershell
cd backend
..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Two Workers Mode (Multi-Worker Scaling Comparison):**
```powershell
cd backend
..\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
```

### 2. Execute Load Test Harness

In a separate terminal, run:

```powershell
.\backend\.venv\Scripts\python.exe evaluation/load_test/load_test.py --worker-config 1_worker
```

Or for 2 workers comparison:

```powershell
.\backend\.venv\Scripts\python.exe evaluation/load_test/load_test.py --worker-config 2_workers
```

## Metrics Collected

- Target Concurrency (1, 10, 25, 50, 100)
- Total Requests & Wall Time
- Successful & Failed Request Counts
- HTTP Status Code Counts (200, 4xx, 5xx)
- Timeout Count (>30s client timeout)
- Requests Per Second (RPS)
- Latency Percentiles (Min, Max, Avg, P50, P95, P99)
- System Resource Usage (CPU %, RAM %)
- API Payload Correctness Validation (Jewellery vs. No-Match 0.80 threshold response)
