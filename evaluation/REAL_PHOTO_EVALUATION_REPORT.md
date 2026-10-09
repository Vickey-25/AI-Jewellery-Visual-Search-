# Real-Photo Evaluation Report — Lumière Visual Search

**Generated**: 2026-10-08T15:30:47.669680  
**Evaluation Mode**: Production SearchService (Service-Level)  
**Total Valid Queries Evaluated**: 80 (Invalid/Excluded: 0)

---

## Executive Summary

- **Recall@1**: 98.8%
- **Recall@5**: 100.0%
- **Recall@10**: 100.0%
- **Mean Reciprocal Rank (MRR)**: 0.9917
- **Category Accuracy (Top-1)**: 100.0%
- **Top-5 Category Purity**: 95.0%
- **P50 Latency**: 119.99 ms | **P95 Latency**: 171.16 ms

---

## Overall Metrics

| Metric | Score | Description |
| :--- | :--- | :--- |
| **Recall@1** | `98.8%` | Expected product (or acceptable duplicate) returned as #1 recommendation |
| **Recall@5** | `100.0%` | Expected product returned in top 5 recommendations |
| **Recall@10** | `100.0%` | Expected product returned in top 10 recommendations |
| **MRR** | `0.9917` | Mean Reciprocal Rank across valid queries |
| **Category Accuracy** | `100.0%` | Top-1 result category matches query jewellery category |
| **Top-5 Category Purity** | `95.0%` | Percentage of top 5 recommendations matching query category |

---

## Per-Category Metrics

| Category | Queries | Recall@1 | Recall@5 | Recall@10 | MRR | Category Acc | Avg Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Bracelet** | 20 | 100.0% | 100.0% | 100.0% | 1.0000 | 100.0% | 121.37 ms |
| **Earrings** | 20 | 95.0% | 100.0% | 100.0% | 0.9667 | 100.0% | 120.98 ms |
| **Necklace** | 20 | 100.0% | 100.0% | 100.0% | 1.0000 | 100.0% | 124.46 ms |
| **Ring** | 20 | 100.0% | 100.0% | 100.0% | 1.0000 | 100.0% | 137.87 ms |

---

## Rank Distribution

| Rank | Query Count | Percentage |
| :--- | :--- | :--- |
| **Rank 1** | 79 | 98.8% |
| **Rank 2** | 0 | 0.0% |
| **Rank 3** | 1 | 1.2% |
| **Rank 4** | 0 | 0.0% |
| **Rank 5** | 0 | 0.0% |
| **Rank 6-10** | 0 | 0.0% |
| **Not Found** | 0 | 0.0% |

---

## Positive Similarity Distribution (Task 9)

| Metric / Percentile | Cosine Similarity Score |
| :--- | :--- |
| **Average Top-1 Similarity** | `0.9265` |
| **Average Correct-Match Similarity** | `0.9264` |
| **Minimum Correct-Match Similarity** | `0.8204` |
| **P10 (10th Percentile)** | `0.8695` |
| **P25 (25th Percentile)** | `0.9063` |
| **Median (P50)** | `0.9329` |
| **P75 (75th Percentile)** | `0.957` |
| **P90 (90th Percentile)** | `0.9747` |
| **Maximum Correct-Match Similarity** | `1.0` |

---

## Non-Jewellery No-Match Analysis & Calibration Status (Task 8)

Initial observation:

The non-jewellery query evaluation (7 test queries) observed top-1 similarity scores below 0.47.

This suggests a potentially useful separation region, but the sample is too small to establish a production threshold.

Threshold calibration requires additional non-jewellery negatives and real jewellery positives.

---

## Latency Breakdown

- **Label**: Production SearchService (Service-Level)
- **P50 (Median) Latency**: `119.99` ms
- **P95 Latency**: `171.16` ms
- **Average Latency**: `126.17` ms
- **Min / Max Latency**: `99.15` ms / `243.67` ms

---

## Invalid / Excluded Ground Truth Rows

*None. All ground-truth rows passed database and file integrity validation.*
