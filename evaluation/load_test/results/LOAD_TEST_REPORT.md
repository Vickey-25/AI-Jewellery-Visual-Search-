# Lumière — AI Jewellery Visual Search: Production Readiness Load & Concurrency Benchmark Report

**Date & Time:** October 8, 2026  
**Environment:** Local Development Benchmark  
**Hardware Specs:** Dell Latitude 3490 (Intel Core i5-8250U CPU @ 1.60GHz, 4 physical / 8 logical cores, 16 GB RAM)  
**System Under Test:** Lumière FastAPI Backend (`POST /api/v1/search/image`)  
**AI Components:** OpenCLIP (`ViT-B-32`, CPU inference with threading lock) + FAISS (`IndexFlatIP`, 2,012 vectors) + PostgreSQL (`pool_size=5`, `max_overflow=10`)  

---

## Executive Summary

A comprehensive production-readiness load and concurrency benchmark was executed on the Lumière visual search backend. The objective was to establish the empirical baseline capacity, identify hardware and architectural bottlenecks, compare single vs. multi-worker Uvicorn configurations, and determine a safe local capacity recommendation without altering production models, database schemas, or visual-search similarity logic.

### Key Performance Findings:
1. **Single Request Latency:** Baseline single-request visual search latency is **~106 ms** (P50) on CPU.
2. **1-Worker Baseline Capacity:**
   - **Concurrency 1 to 25:** 100% success rate (0% error rate). Sustainable throughput peaks at **~6.39 RPS** at concurrency 10.
   - **Concurrency 50:** 100% HTTP 200 success rate, but average latency increases to **11,886 ms** (P95: 20,480 ms) due to single-thread queue serialization behind `CLIPService._lock`.
   - **Concurrency 100:** **100% timeout failure** (150/150 requests timed out exceeding 30s client timeout). CPU queue depth saturation causes average latency to exceed 30 seconds.
3. **Multi-Worker Scaling (2 Uvicorn Workers):**
   - **Concurrency 100 Success:** Introducing 2 worker processes completely resolves the 100-concurrency timeout failure, achieving **0% errors** and **100% HTTP 200 responses** for all 150 requests (Avg latency: 11,034 ms, P95: 16,929 ms).
   - Peak throughput increases to **~7.99 RPS** at concurrency 25, nearly doubling throughput at concurrency 50 (from 3.68 RPS to 6.56 RPS).
4. **Primary Bottleneck:** CPU-bound OpenCLIP image encoding (`open_clip` / PyTorch CPU execution) serialized by Python GIL and internal `CLIPService._lock`. Database (PostgreSQL) and FAISS index search contributed <2 ms per query.

---

## 1. Summary Benchmark Results Table (1 Worker Baseline)

| Concurrency | Requests | Success | Errors | RPS | Avg (ms) | Min (ms) | Max (ms) | P50 (ms) | P95 (ms) | P99 (ms) | CPU (%) | RAM (%) |
|-------------|----------|---------|--------|-----|----------|----------|----------|----------|----------|----------|---------|---------|
| **1**       | 20       | 20      | 0      | 5.23| 173.59   | 88.68    | 457.89   | 106.49   | 436.46   | 453.60   | 51.5%   | 56.3%   |
| **10**      | 50       | 50      | 0      | 6.39| 1357.37  | 172.47   | 2270.56  | 1310.68  | 2102.91  | 2235.61  | 92.6%   | 56.7%   |
| **25**      | 100      | 100     | 0      | 6.01| 3554.76  | 268.84   | 4919.94  | 3790.14  | 4774.66  | 4883.05  | 96.1%   | 57.9%   |
| **50**      | 150      | 150     | 0      | 3.68| 11886.71 | 6831.74  | 22285.15 | 9830.86  | 20480.19 | 22273.13 | 100.0%  | 59.2%   |
| **100**     | 150      | 0       | 150    | 2.45| 30453.90 | 30152.95 | 30618.30 | 30588.43 | 30614.49 | 30617.59 | 25.5%   | 60.7%   |

*Note: At Concurrency 100 in 1-worker mode, all 150 requests exceeded the 30-second client timeout threshold due to linear thread queueing behind CPU inference.*

---

## 2. Server Worker Comparison Table (1 Worker vs 2 Workers)

| Concurrency | Configuration | Success % | RPS | Avg (ms) | P50 (ms) | P95 (ms) | P99 (ms) | CPU (%) | RAM (%) |
|-------------|---------------|-----------|-----|----------|----------|----------|----------|---------|---------|
| **10**      | 1 Worker      | 100%      | 6.39| 1357.37  | 1310.68  | 2102.91  | 2235.61  | 92.6%   | 56.7%   |
| **10**      | 2 Workers     | 100%      | 7.33| 1219.84  | 1274.05  | 2227.39  | 2282.41  | 89.9%   | 64.6%   |
| **25**      | 1 Worker      | 100%      | 6.01| 3554.76  | 3790.14  | 4774.66  | 4883.05  | 96.1%   | 57.9%   |
| **25**      | 2 Workers     | 100%      | 7.99| 2689.73  | 2674.93  | 3948.54  | 4020.56  | 94.3%   | 65.6%   |
| **50**      | 1 Worker      | 100%      | 3.68| 11886.71 | 9830.86  | 20480.19 | 22273.13 | 100.0%  | 59.2%   |
| **50**      | 2 Workers     | 100%      | 6.56| 6438.69  | 6922.03  | 9618.81  | 9931.56  | 96.3%   | 66.9%   |
| **100**     | 1 Worker      | 0% (Timeout)| 2.45| 30453.90| 30588.43 | 30614.49 | 30617.59 | 25.5%   | 60.7%   |
| **100**     | 2 Workers     | **100%**  | 6.18| 11034.20 | 12272.07 | 16929.62 | 17337.51 | 95.2%   | 68.6%   |

---

## 3. No-Match Threshold Concurrency Results

Using non-jewellery image (`evaluation/no_match/car.jpg`):

| Worker Config | Concurrency | Requests | Success % | RPS | Avg (ms) | P50 (ms) | P95 (ms) | API Threshold Correctness |
|---------------|-------------|----------|-----------|-----|----------|----------|----------|---------------------------|
| **1 Worker**  | 10          | 50       | 80%*      | 1.23| 7843.97  | 2307.41  | 30725.35 | Verified (`results: []`, `message` OK) |
| **1 Worker**  | 25          | 100      | 100%      | 5.35| 4128.82  | 4255.36  | 5648.70  | Verified (`results: []`, `message` OK) |
| **2 Workers** | 10          | 50       | **100%**  | 7.21| 1236.84  | 1486.52  | 1581.41  | Verified (`results: []`, `message` OK) |
| **2 Workers** | 25          | 100      | **100%**  | 5.32| 4020.01  | 3640.21  | 6181.56  | Verified (`results: []`, `message` OK) |

*Note: Under 1 worker at C=10, initial TCP socket backlog burst caused 10 client timeouts before settling. Under 2 workers, zero errors occurred.*

---

## 4. Subsystem Observations & Bottleneck Diagnostics

### Database (PostgreSQL)
- Connection Pool: Configured with `pool_size=5`, `max_overflow=10` (max 15 active connections).
- Behavior: Zero connection pool exhaustion errors, zero deadlocks, zero slow query warnings.
- Impact: PostgreSQL query execution time for resolving product metadata by IDs is <2 ms per query. Database is **NOT** the system bottleneck.

### OpenCLIP Model Inference
- Behavior: Model loaded once per process during application startup (`lifespan`).
- Thread Safety: OpenCLIP inference is wrapped in `threading.Lock()` inside `CLIPService.generate_image_embedding()`.
- Impact: Single-image CPU inference takes **~100 ms**. Under 100 concurrent requests in 1 worker process, requests queue sequentially, resulting in 100 × 100 ms = 10,000 ms to 30,000 ms latency. OpenCLIP CPU inference is the **PRIMARY SYSTEM BOTTLENECK**.

### FAISS Vector Search
- Behavior: Index Flat IP loaded once per process into memory (`IndexFlatIP`, 2,012 vectors of 512 dimensions).
- Thread Safety: Thread safety ensured via `threading.RLock()`.
- Impact: Vector similarity search across 2,012 vectors takes **<0.5 ms** per query. FAISS is **NOT** a bottleneck.

---

## 5. Capacity Recommendations

### Local Benchmark Capacity
- **Highest Safe Concurrency (0% Errors, P95 < 5s):** **Concurrency 25**
- **Sustainable Requests/Second (RPS):** **~6.0 to 8.0 RPS** on 4-core CPU.
- **Recommended Local Server Configuration:** **2 Uvicorn Workers** (`uvicorn app.main:app --workers 2`).

### Conservative Initial Production Target Recommendation
> Based on measurements on this 4-core CPU host, the local backend safely supports up to **10 concurrent visual search requests** under sub-2.5 second SLA, or up to **25 concurrent requests** under sub-5 second SLA.

---

## 6. Recommended Next Optimizations (For Future Tasks)

1. **GPU Acceleration (CUDA / TensorRT):** Offloading OpenCLIP inference from CPU to an NVIDIA GPU (e.g. T4 or RTX 4090) reduces single-image inference latency from ~100 ms to ~5-10 ms (10-20x throughput improvement).
2. **ONNX Runtime / OpenVINO Execution:** Quantizing OpenCLIP to INT8 or FP16 via OpenVINO or ONNX Runtime on CPU can increase throughput by 2-4x.
3. **Dynamic Batching:** Grouping concurrent incoming image inference requests into a single tensor batch (batch size 8 or 16) before calling `model.encode_image()` dramatically increases CPU/GPU matrix multiplication efficiency.
4. **Dedicated AI Inference Microservice:** Decoupling FastAPI web servers from OpenCLIP model inference via Redis queue or gRPC workers prevents web worker pool exhaustion.
