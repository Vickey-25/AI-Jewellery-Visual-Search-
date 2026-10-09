"""Automated Real-Photo Evaluation System for Lumière AI Jewellery Visual Search.

Measures Recall@1, Recall@5, Recall@10, MRR, Category Accuracy, Category Purity,
Rank Distribution, Similarity Score distributions, and Latency breakdown on real customer photos.

Usage:
  python evaluation/evaluate_real_photos.py [--api] [--top-k 10]
"""

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

from PIL import Image

# Ensure backend directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.clip_service import CLIPService
from app.ai.faiss_index import FaissIndex
from app.config import settings
from app.database.database import SessionLocal
from app.database.models import Product
from app.services.product_service import ProductFilters
from app.services.search_service import SearchService
from app.utils.image_utils import prepare_for_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("evaluate_real_photos")

EVAL_DIR = BASE_DIR / "evaluation"
DEFAULT_CSV_PATH = EVAL_DIR / "real_photo_ground_truth.csv"
DEFAULT_PHOTOS_DIR = EVAL_DIR / "real_photos"

VALID_CATEGORIES = {"ring", "rings", "necklace", "necklaces", "bracelet", "bracelets", "earring", "earrings"}


def find_query_image(query_filename: str, photos_dir: Path) -> Optional[Path]:
    """Locate query image file across evaluation directories."""
    candidates = [
        photos_dir / query_filename,
        photos_dir / query_filename.lower(),
        EVAL_DIR / "queries" / Path(query_filename).name,
        EVAL_DIR / Path(query_filename),
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def parse_acceptable_ids(row: dict, default_id: int) -> Set[int]:
    """Parse pipe-separated acceptable product IDs for duplicate handling."""
    acceptable = {default_id}
    raw = row.get("acceptable_product_ids", "").strip()
    if raw:
        for part in raw.split("|"):
            part_str = part.strip()
            if part_str.isdigit():
                acceptable.add(int(part_str))
    return acceptable


def validate_ground_truth(
    csv_path: Path, photos_dir: Path, db_session
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Validate ground truth rows against PostgreSQL and local image files (Task 2 & 22)."""
    if not csv_path.is_file():
        logger.error(f"Ground truth CSV not found: {csv_path}")
        return [], []

    active_products = dict(
        db_session.query(Product.id, Product).filter(Product.is_active.is_(True)).all()
    )

    valid_rows = []
    invalid_rows = []

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):
            q_img_name = row.get("query_image", "").strip()
            category = row.get("category", "").strip()
            exp_id_str = row.get("expected_product_id", "").strip()
            exp_code = row.get("expected_product_code", "").strip()

            if not q_img_name or not exp_id_str or not exp_code:
                invalid_rows.append(
                    {"line": line_num, "row": row, "reason": "Missing required CSV columns"}
                )
                continue

            try:
                exp_id = int(exp_id_str)
            except ValueError:
                invalid_rows.append(
                    {"line": line_num, "row": row, "reason": f"Invalid expected_product_id '{exp_id_str}'"}
                )
                continue

            img_path = find_query_image(q_img_name, photos_dir)
            if not img_path:
                invalid_rows.append(
                    {"line": line_num, "row": row, "reason": f"Image file missing on disk: '{q_img_name}'"}
                )
                continue

            prod = active_products.get(exp_id)
            if not prod:
                invalid_rows.append(
                    {"line": line_num, "row": row, "reason": f"Product ID {exp_id} not found in PostgreSQL active catalog"}
                )
                continue

            if prod.product_code != exp_code:
                invalid_rows.append(
                    {
                        "line": line_num,
                        "row": row,
                        "reason": f"Product code mismatch: CSV has '{exp_code}', DB has '{prod.product_code}'",
                    }
                )
                continue

            if category.lower() not in VALID_CATEGORIES:
                invalid_rows.append(
                    {"line": line_num, "row": row, "reason": f"Unrecognized category '{category}'"}
                )
                continue

            acceptable_ids = parse_acceptable_ids(row, exp_id)

            valid_rows.append({
                "line": line_num,
                "query_image": q_img_name,
                "img_path": img_path,
                "category": category,
                "expected_product_id": exp_id,
                "expected_product_code": exp_code,
                "acceptable_product_ids": acceptable_ids,
            })

    return valid_rows, invalid_rows


def evaluate_via_service(
    valid_rows: List[Dict[str, Any]], top_k: int = 10
) -> Tuple[List[Dict[str, Any]], str]:
    """Execute evaluation directly using production SearchService."""
    logger.info("Initializing production CLIPService and FAISSIndex for evaluation...")
    clip = CLIPService(
        settings.model_name,
        settings.model_pretrained,
        settings.model_device,
        settings.torch_num_threads,
    )
    faiss_idx = FaissIndex(settings.faiss_index_path, settings.faiss_mapping_path)
    if not faiss_idx.load():
        raise RuntimeError("Could not load FAISS index. Run scripts/create_index.py first.")

    service = SearchService(clip, faiss_idx, 0.6, 0.4)
    filters = ProductFilters.clean()

    eval_results = []
    with SessionLocal() as db:
        for idx, item in enumerate(valid_rows, start=1):
            img_path: Path = item["img_path"]
            exp_id: int = item["expected_product_id"]
            acceptable: Set[int] = item["acceptable_product_ids"]
            cat: str = item["category"]

            t0 = time.perf_counter()
            with Image.open(img_path) as raw:
                raw.load()
                prepared = prepare_for_model(raw)
            search_res = service.search_by_image(db, prepared, top_k=top_k, filters=filters)
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0

            rank_found = None
            expected_sim = None
            for rank, r in enumerate(search_res, start=1):
                if r.product_id in acceptable:
                    rank_found = rank
                    expected_sim = r.similarity
                    break

            top1_res = search_res[0] if search_res else None
            top1_id = top1_res.product_id if top1_res else None
            top1_code = top1_res.product_code if top1_res else ""
            top1_cat = top1_res.category if top1_res else ""
            top1_sim = top1_res.similarity if top1_res else 0.0

            cat_lower = cat.lower().rstrip("s")
            top5_matches = sum(
                1 for r in search_res[:5] if r.category.lower().rstrip("s") == cat_lower
            )
            top10_matches = sum(
                1 for r in search_res[:10] if r.category.lower().rstrip("s") == cat_lower
            )

            eval_results.append({
                "query_image": item["query_image"],
                "category": cat,
                "expected_product_id": exp_id,
                "expected_product_code": item["expected_product_code"],
                "acceptable_product_ids": item["acceptable_product_ids"],
                "rank_found": rank_found,
                "reciprocal_rank": (1.0 / rank_found) if rank_found else 0.0,
                "recall_at_1": 1 if (rank_found == 1) else 0,
                "recall_at_5": 1 if (rank_found and rank_found <= 5) else 0,
                "recall_at_10": 1 if (rank_found and rank_found <= 10) else 0,
                "top1_product_id": top1_id,
                "top1_product_code": top1_code,
                "top1_category": top1_cat,
                "top1_similarity": top1_sim,
                "expected_product_similarity": expected_sim,
                "category_correct": 1 if (top1_cat.lower().rstrip("s") == cat_lower) else 0,
                "top5_category_purity": top5_matches / min(5, len(search_res)) if search_res else 0,
                "top10_category_purity": top10_matches / min(10, len(search_res)) if search_res else 0,
                "latency_ms": latency_ms,
            })

    return eval_results, "Production SearchService (Service-Level)"


def evaluate_via_api(
    valid_rows: List[Dict[str, Any]], top_k: int = 10, api_url: str = "http://127.0.0.1:8000"
) -> Tuple[List[Dict[str, Any]], str]:
    """Execute evaluation via HTTP REST API endpoint (POST /api/v1/search/image)."""
    import httpx
    endpoint = f"{api_url.rstrip('/')}/api/v1/search/image"
    logger.info(f"Connecting to visual search API endpoint: {endpoint}...")

    eval_results = []
    with httpx.Client(timeout=30.0) as client:
        for idx, item in enumerate(valid_rows, start=1):
            img_path: Path = item["img_path"]
            exp_id: int = item["expected_product_id"]
            acceptable: Set[int] = item["acceptable_product_ids"]
            cat: str = item["category"]

            t0 = time.perf_counter()
            with open(img_path, "rb") as f:
                files = {"image": (img_path.name, f, "image/jpeg")}
                data = {"top_k": str(top_k)}
                resp = client.post(endpoint, files=files, data=data)
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0

            if resp.status_code != 200:
                logger.warning(f"API request failed for {img_path.name}: HTTP {resp.status_code}")
                continue

            res_data = resp.json()
            search_res = res_data.get("results", [])

            rank_found = None
            expected_sim = None
            for rank, r in enumerate(search_res, start=1):
                pid = r.get("product_id")
                if pid in acceptable:
                    rank_found = rank
                    expected_sim = r.get("similarity")
                    break

            top1_res = search_res[0] if search_res else {}
            top1_id = top1_res.get("product_id")
            top1_code = top1_res.get("product_code", "")
            top1_cat = top1_res.get("category", "")
            top1_sim = top1_res.get("similarity", 0.0)

            cat_lower = cat.lower().rstrip("s")
            top5_matches = sum(
                1 for r in search_res[:5] if r.get("category", "").lower().rstrip("s") == cat_lower
            )
            top10_matches = sum(
                1 for r in search_res[:10] if r.get("category", "").lower().rstrip("s") == cat_lower
            )

            eval_results.append({
                "query_image": item["query_image"],
                "category": cat,
                "expected_product_id": exp_id,
                "expected_product_code": item["expected_product_code"],
                "acceptable_product_ids": item["acceptable_product_ids"],
                "rank_found": rank_found,
                "reciprocal_rank": (1.0 / rank_found) if rank_found else 0.0,
                "recall_at_1": 1 if (rank_found == 1) else 0,
                "recall_at_5": 1 if (rank_found and rank_found <= 5) else 0,
                "recall_at_10": 1 if (rank_found and rank_found <= 10) else 0,
                "top1_product_id": top1_id,
                "top1_product_code": top1_code,
                "top1_category": top1_cat,
                "top1_similarity": top1_sim,
                "expected_product_similarity": expected_sim,
                "category_correct": 1 if (top1_cat.lower().rstrip("s") == cat_lower) else 0,
                "top5_category_purity": top5_matches / min(5, len(search_res)) if search_res else 0,
                "top10_category_purity": top10_matches / min(10, len(search_res)) if search_res else 0,
                "latency_ms": latency_ms,
            })

    return eval_results, f"HTTP REST API ({endpoint})"


def compute_metrics(
    eval_results: List[Dict[str, Any]], invalid_rows: List[Dict[str, Any]], mode_label: str
) -> Dict[str, Any]:
    """Compute overall, per-category, rank distribution, similarity, and latency metrics."""
    n_valid = len(eval_results)
    if n_valid == 0:
        return {"error": "No valid ground truth rows to evaluate."}

    rec1 = sum(r["recall_at_1"] for r in eval_results) / n_valid
    rec5 = sum(r["recall_at_5"] for r in eval_results) / n_valid
    rec10 = sum(r["recall_at_10"] for r in eval_results) / n_valid
    mrr = sum(r["reciprocal_rank"] for r in eval_results) / n_valid
    cat_acc = sum(r["category_correct"] for r in eval_results) / n_valid

    avg_purity5 = sum(r["top5_category_purity"] for r in eval_results) / n_valid
    avg_purity10 = sum(r["top10_category_purity"] for r in eval_results) / n_valid

    # Latency breakdown
    latencies = [r["latency_ms"] for r in eval_results]
    latencies_sorted = sorted(latencies)
    avg_lat = sum(latencies) / n_valid
    p50_lat = latencies_sorted[int(n_valid * 0.50)]
    p95_lat = latencies_sorted[int(n_valid * 0.95)] if n_valid >= 20 else latencies_sorted[-1]
    min_lat = latencies_sorted[0]
    max_lat = latencies_sorted[-1]

    # Similarity scores & Task 9 Positive Similarity Distribution Percentiles
    top1_sims = [r["top1_similarity"] for r in eval_results]
    avg_top1_sim = sum(top1_sims) / n_valid

    correct_sims = [
        r["expected_product_similarity"]
        for r in eval_results
        if r["expected_product_similarity"] is not None
    ]
    if correct_sims:
        cs_sorted = sorted(correct_sims)
        n_cs = len(cs_sorted)
        p10_sim = cs_sorted[int(n_cs * 0.10)]
        p25_sim = cs_sorted[int(n_cs * 0.25)]
        median_sim = cs_sorted[int(n_cs * 0.50)]
        p75_sim = cs_sorted[int(n_cs * 0.75)]
        p90_sim = cs_sorted[int(n_cs * 0.90)]
        min_correct_sim = cs_sorted[0]
        max_correct_sim = cs_sorted[-1]
        avg_correct_sim = sum(correct_sims) / n_cs
    else:
        p10_sim = p25_sim = median_sim = p75_sim = p90_sim = min_correct_sim = max_correct_sim = avg_correct_sim = 0.0

    # Rank distribution
    rank_dist = {f"Rank {i}": 0 for i in range(1, 6)}
    rank_dist["Rank 6-10"] = 0
    rank_dist["Not Found"] = 0

    for r in eval_results:
        rf = r["rank_found"]
        if rf is None:
            rank_dist["Not Found"] += 1
        elif 1 <= rf <= 5:
            rank_dist[f"Rank {rf}"] += 1
        elif 6 <= rf <= 10:
            rank_dist["Rank 6-10"] += 1

    # Per-category metrics
    by_cat: Dict[str, List[Dict[str, Any]]] = {}
    for r in eval_results:
        c = r["category"].capitalize()
        if c.endswith("s") and c != "Earrings":
            c = c[:-1]
        by_cat.setdefault(c, []).append(r)

    category_stats = {}
    for cat_name, cat_items in by_cat.items():
        cn = len(cat_items)
        c_rec1 = sum(x["recall_at_1"] for x in cat_items) / cn
        c_rec5 = sum(x["recall_at_5"] for x in cat_items) / cn
        c_rec10 = sum(x["recall_at_10"] for x in cat_items) / cn
        c_mrr = sum(x["reciprocal_rank"] for x in cat_items) / cn
        c_acc = sum(x["category_correct"] for x in cat_items) / cn
        c_lat = sum(x["latency_ms"] for x in cat_items) / cn

        category_stats[cat_name] = {
            "queries": cn,
            "recall_at_1": round(c_rec1, 4),
            "recall_at_5": round(c_rec5, 4),
            "recall_at_10": round(c_rec10, 4),
            "mrr": round(c_mrr, 4),
            "category_accuracy": round(c_acc, 4),
            "average_latency_ms": round(c_lat, 2),
        }

    failed_queries = [
        {
            "query_image": r["query_image"],
            "expected_code": r["expected_product_code"],
            "category": r["category"],
            "rank_found": r["rank_found"] if r["rank_found"] else "Not Found",
            "top1_similarity": round(r["top1_similarity"], 4),
        }
        for r in eval_results
        if r["recall_at_10"] == 0
    ]

    summary = {
        "timestamp": datetime.now().isoformat(),
        "evaluation_mode": mode_label,
        "total_queries_submitted": len(eval_results) + len(invalid_rows),
        "valid_queries": n_valid,
        "invalid_queries": len(invalid_rows),
        "overall_metrics": {
            "recall_at_1": round(rec1, 4),
            "recall_at_5": round(rec5, 4),
            "recall_at_10": round(rec10, 4),
            "mrr": round(mrr, 4),
            "category_accuracy": round(cat_acc, 4),
            "top5_category_purity": round(avg_purity5, 4),
            "top10_category_purity": round(avg_purity10, 4),
        },
        "positive_similarity_distribution": {
            "average_top1_similarity": round(avg_top1_sim, 4),
            "average_correct_match_similarity": round(avg_correct_sim, 4),
            "min_correct_match_similarity": round(min_correct_sim, 4),
            "p10_correct_match_similarity": round(p10_sim, 4),
            "p25_correct_match_similarity": round(p25_sim, 4),
            "median_correct_match_similarity": round(median_sim, 4),
            "p75_correct_match_similarity": round(p75_sim, 4),
            "p90_correct_match_similarity": round(p90_sim, 4),
            "max_correct_match_similarity": round(max_correct_sim, 4),
        },
        "latency_ms": {
            "label": mode_label,
            "average_ms": round(avg_lat, 2),
            "p50_ms": round(p50_lat, 2),
            "p95_ms": round(p95_lat, 2),
            "min_ms": round(min_lat, 2),
            "max_ms": round(max_lat, 2),
        },
        "rank_distribution": rank_dist,
        "category_metrics": category_stats,
        "failed_queries_count": len(failed_queries),
        "invalid_rows_detail": invalid_rows,
    }

    return summary


def write_results_files(
    eval_results: List[Dict[str, Any]], summary: Dict[str, Any]
) -> Tuple[Path, Path, Path]:
    """Save evaluation_results.csv, evaluation_summary.json, and REAL_PHOTO_EVALUATION_REPORT.md."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Write evaluation_results.csv
    csv_out = EVAL_DIR / "evaluation_results.csv"
    fieldnames = [
        "query_image",
        "category",
        "expected_product_id",
        "expected_product_code",
        "rank_found",
        "reciprocal_rank",
        "recall_at_1",
        "recall_at_5",
        "recall_at_10",
        "top1_product_id",
        "top1_product_code",
        "top1_category",
        "top1_similarity",
        "expected_product_similarity",
        "latency_ms",
    ]
    with open(csv_out, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in eval_results:
            row = {k: r.get(k, "") for k in fieldnames}
            row["latency_ms"] = round(row["latency_ms"], 2)
            if row["reciprocal_rank"]:
                row["reciprocal_rank"] = round(row["reciprocal_rank"], 4)
            if row["top1_similarity"]:
                row["top1_similarity"] = round(row["top1_similarity"], 4)
            if row["expected_product_similarity"] is not None:
                row["expected_product_similarity"] = round(row["expected_product_similarity"], 4)
            writer.writerow(row)

    # 2. Write evaluation_summary.json
    json_out = EVAL_DIR / "evaluation_summary.json"
    with open(json_out, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 3. Write REAL_PHOTO_EVALUATION_REPORT.md (Task 8, 9, 10)
    md_out = EVAL_DIR / "REAL_PHOTO_EVALUATION_REPORT.md"
    ov = summary["overall_metrics"]
    lat = summary["latency_ms"]
    psim = summary["positive_similarity_distribution"]
    rd = summary["rank_distribution"]
    cats = summary["category_metrics"]

    md_lines = [
        "# Real-Photo Evaluation Report — Lumière Visual Search\n",
        f"**Generated**: {summary['timestamp']}  ",
        f"**Evaluation Mode**: {summary['evaluation_mode']}  ",
        f"**Total Valid Queries Evaluated**: {summary['valid_queries']} (Invalid/Excluded: {summary['invalid_queries']})\n",
        "---\n",
        "## Executive Summary\n",
        f"- **Recall@1**: {ov['recall_at_1'] * 100:.1f}%",
        f"- **Recall@5**: {ov['recall_at_5'] * 100:.1f}%",
        f"- **Recall@10**: {ov['recall_at_10'] * 100:.1f}%",
        f"- **Mean Reciprocal Rank (MRR)**: {ov['mrr']:.4f}",
        f"- **Category Accuracy (Top-1)**: {ov['category_accuracy'] * 100:.1f}%",
        f"- **Top-5 Category Purity**: {ov['top5_category_purity'] * 100:.1f}%",
        f"- **P50 Latency**: {lat['p50_ms']} ms | **P95 Latency**: {lat['p95_ms']} ms\n",
        "---\n",
        "## Overall Metrics\n",
        "| Metric | Score | Description |",
        "| :--- | :--- | :--- |",
        f"| **Recall@1** | `{ov['recall_at_1'] * 100:.1f}%` | Expected product (or acceptable duplicate) returned as #1 recommendation |",
        f"| **Recall@5** | `{ov['recall_at_5'] * 100:.1f}%` | Expected product returned in top 5 recommendations |",
        f"| **Recall@10** | `{ov['recall_at_10'] * 100:.1f}%` | Expected product returned in top 10 recommendations |",
        f"| **MRR** | `{ov['mrr']:.4f}` | Mean Reciprocal Rank across valid queries |",
        f"| **Category Accuracy** | `{ov['category_accuracy'] * 100:.1f}%` | Top-1 result category matches query jewellery category |",
        f"| **Top-5 Category Purity** | `{ov['top5_category_purity'] * 100:.1f}%` | Percentage of top 5 recommendations matching query category |\n",
        "---\n",
        "## Per-Category Metrics\n",
        "| Category | Queries | Recall@1 | Recall@5 | Recall@10 | MRR | Category Acc | Avg Latency |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    for cname, cstat in cats.items():
        md_lines.append(
            f"| **{cname}** | {cstat['queries']} | {cstat['recall_at_1']*100:.1f}% | {cstat['recall_at_5']*100:.1f}% | {cstat['recall_at_10']*100:.1f}% | {cstat['mrr']:.4f} | {cstat['category_accuracy']*100:.1f}% | {cstat['average_latency_ms']} ms |"
        )

    md_lines.extend([
        "\n---\n",
        "## Rank Distribution\n",
        "| Rank | Query Count | Percentage |",
        "| :--- | :--- | :--- |",
    ])
    for rname, rcnt in rd.items():
        pct = (rcnt / summary['valid_queries']) * 100 if summary['valid_queries'] else 0
        md_lines.append(f"| **{rname}** | {rcnt} | {pct:.1f}% |")

    md_lines.extend([
        "\n---\n",
        "## Positive Similarity Distribution (Task 9)\n",
        "| Metric / Percentile | Cosine Similarity Score |",
        "| :--- | :--- |",
        f"| **Average Top-1 Similarity** | `{psim['average_top1_similarity']}` |",
        f"| **Average Correct-Match Similarity** | `{psim['average_correct_match_similarity']}` |",
        f"| **Minimum Correct-Match Similarity** | `{psim['min_correct_match_similarity']}` |",
        f"| **P10 (10th Percentile)** | `{psim['p10_correct_match_similarity']}` |",
        f"| **P25 (25th Percentile)** | `{psim['p25_correct_match_similarity']}` |",
        f"| **Median (P50)** | `{psim['median_correct_match_similarity']}` |",
        f"| **P75 (75th Percentile)** | `{psim['p75_correct_match_similarity']}` |",
        f"| **P90 (90th Percentile)** | `{psim['p90_correct_match_similarity']}` |",
        f"| **Maximum Correct-Match Similarity** | `{psim['max_correct_match_similarity']}` |\n",
        "---\n",
        "## Non-Jewellery No-Match Analysis & Calibration Status (Task 8)\n",
        "Initial observation:\n",
        "The non-jewellery query evaluation (7 test queries) observed top-1 similarity scores below 0.47.\n",
        "This suggests a potentially useful separation region, but the sample is too small to establish a production threshold.\n",
        "Threshold calibration requires additional non-jewellery negatives and real jewellery positives.\n",
        "---\n",
        "## Latency Breakdown\n",
        f"- **Label**: {lat['label']}",
        f"- **P50 (Median) Latency**: `{lat['p50_ms']}` ms",
        f"- **P95 Latency**: `{lat['p95_ms']}` ms",
        f"- **Average Latency**: `{lat['average_ms']}` ms",
        f"- **Min / Max Latency**: `{lat['min_ms']}` ms / `{lat['max_ms']}` ms\n",
        "---\n",
        "## Invalid / Excluded Ground Truth Rows\n",
    ])

    if summary["invalid_queries"] == 0:
        md_lines.append("*None. All ground-truth rows passed database and file integrity validation.*\n")
    else:
        md_lines.append(f"Total invalid rows excluded: `{summary['invalid_queries']}`\n")
        for inv in summary["invalid_rows_detail"]:
            md_lines.append(f"- Line {inv['line']}: {inv['reason']}")

    with open(md_out, mode="w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    return csv_out, json_out, md_out


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Lumière AI Jewellery Visual Search on real customer photos.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to ground truth CSV")
    parser.add_argument("--photos-dir", type=Path, default=DEFAULT_PHOTOS_DIR, help="Path to real photos directory")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K recommendations to request (default: 10)")
    parser.add_argument("--api", action="store_true", help="Run evaluation via HTTP REST API endpoint")
    parser.add_argument("--api-url", type=str, default="http://127.0.0.1:8000", help="Base URL for REST API evaluation")
    args = parser.parse_args()

    print("=" * 60)
    print("      LUMIÈRE REAL-PHOTO EVALUATION SYSTEM")
    print("=" * 60)
    print(f"Ground Truth CSV: {args.csv}")
    print(f"Real Photos Dir:  {args.photos_dir}")

    with SessionLocal() as db_session:
        valid_rows, invalid_rows = validate_ground_truth(args.csv, args.photos_dir, db_session)

    print(f"Validation summary: {len(valid_rows)} valid ground truth rows, {len(invalid_rows)} invalid/excluded rows.")
    if invalid_rows:
        for inv in invalid_rows:
            print(f"  [INVALID Line {inv['line']}]: {inv['reason']}")

    if not valid_rows:
        print("\nNo valid ground truth rows found. Please verify real_photo_ground_truth.csv and photo files.")
        return 1

    print(f"\nExecuting evaluation on {len(valid_rows)} valid queries (top_k={args.top_k})...")
    if args.api:
        eval_results, mode_label = evaluate_via_api(valid_rows, top_k=args.top_k, api_url=args.api_url)
    else:
        eval_results, mode_label = evaluate_via_service(valid_rows, top_k=args.top_k)

    summary = compute_metrics(eval_results, invalid_rows, mode_label)
    csv_out, json_out, md_out = write_results_files(eval_results, summary)

    # Task 6: Print at least 10 example queries with details
    print("\n" + "=" * 60)
    print("          TASK 6: EXAMPLE QUERY VERIFICATION (10 SAMPLES)")
    print("=" * 60)
    for sample in eval_results[:10]:
        acc_str = ",".join(str(i) for i in sorted(list(sample["acceptable_product_ids"])))
        print(f"Query:        {sample['query_image']}")
        print(f"Expected:     {sample['expected_product_id']} / {sample['expected_product_code']}")
        print(f"Acceptable:   {acc_str}")
        print(f"Top result:   {sample['top1_product_id']} / {sample['top1_product_code']}")
        print(f"Correct rank: {sample['rank_found'] if sample['rank_found'] else 'Not Found'}")
        print(f"Recall@1:     {sample['recall_at_1']}")
        print(f"Recall@5:     {sample['recall_at_5']}")
        print(f"Recall@10:    {sample['recall_at_10']}")
        print(f"RR:           {sample['reciprocal_rank']:.4f}")
        print("-" * 40)

    # Task 7: Print Rank Distribution
    print("\n" + "=" * 60)
    print("          TASK 7: RANK DISTRIBUTION")
    print("=" * 60)
    rd = summary["rank_distribution"]
    for rname, rcnt in rd.items():
        pct = (rcnt / summary['valid_queries']) * 100 if summary['valid_queries'] else 0
        print(f"  {rname}: {rcnt} ({pct:.1f}%)")

    # Task 9: Print Positive Similarity Distribution Percentiles
    psim = summary["positive_similarity_distribution"]
    print("\n" + "=" * 60)
    print("      TASK 9: POSITIVE SIMILARITY DISTRIBUTION")
    print("=" * 60)
    print(f"  Min Correct Match Sim:    {psim['min_correct_match_similarity']}")
    print(f"  P10:                      {psim['p10_correct_match_similarity']}")
    print(f"  P25:                      {psim['p25_correct_match_similarity']}")
    print(f"  Median (P50):             {psim['median_correct_match_similarity']}")
    print(f"  P75:                      {psim['p75_correct_match_similarity']}")
    print(f"  P90:                      {psim['p90_correct_match_similarity']}")
    print(f"  Max Correct Match Sim:    {psim['max_correct_match_similarity']}")

    ov = summary["overall_metrics"]
    lat = summary["latency_ms"]

    print("\n" + "=" * 60)
    print("                OVERALL EVALUATION RESULTS")
    print("=" * 60)
    print(f"Mode:              {mode_label}")
    print(f"Valid Queries:     {summary['valid_queries']}")
    print(f"Recall@1:          {ov['recall_at_1'] * 100:.1f}%")
    print(f"Recall@5:          {ov['recall_at_5'] * 100:.1f}%")
    print(f"Recall@10:         {ov['recall_at_10'] * 100:.1f}%")
    print(f"MRR:               {ov['mrr']:.4f}")
    print(f"Category Accuracy: {ov['category_accuracy'] * 100:.1f}%")
    print(f"P50 Latency:       {lat['p50_ms']} ms")
    print(f"P95 Latency:       {lat['p95_ms']} ms")
    print("=" * 60)
    print(f"CSV Output:     {csv_out}")
    print(f"JSON Output:    {json_out}")
    print(f"Report Output:  {md_out}")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
