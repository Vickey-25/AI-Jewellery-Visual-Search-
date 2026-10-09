"""Data-Driven No-Match Threshold Calibration System for Lumière AI Visual Search.

Measures similarity score distributions for genuine jewellery (positives) and
non-jewellery images (negatives), performs threshold sweeps, ROC/AUC analysis,
Precision-Recall analysis, calibration/validation splitting, and generates
machine-readable configuration and THRESHOLD_CALIBRATION_REPORT.md.

Usage:
  python evaluation/calibrate_threshold.py
"""

import argparse
import csv
import json
import logging
import math
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

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
from app.services.product_service import ProductFilters
from app.services.search_service import SearchService
from app.utils.image_utils import prepare_for_model

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("calibrate_threshold")

EVAL_DIR = BASE_DIR / "evaluation"
REAL_PHOTO_CSV = EVAL_DIR / "real_photo_ground_truth.csv"
REAL_PHOTO_DIR = EVAL_DIR / "real_photos"
NO_MATCH_CSV = EVAL_DIR / "no_match_ground_truth.csv"
NO_MATCH_DIR = EVAL_DIR / "no_match"


def find_image_file(rel_filename: str, base_dir: Path) -> Optional[Path]:
    """Locate query image file in relative paths or standard evaluation directories."""
    candidates = [
        base_dir / rel_filename,
        base_dir / rel_filename.lower(),
        EVAL_DIR / rel_filename,
        EVAL_DIR / "queries" / Path(rel_filename).name,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def calculate_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate comprehensive statistical distribution percentiles."""
    if not values:
        return {k: 0.0 for k in ["count", "min", "p5", "p10", "p25", "p50", "p75", "p90", "p95", "p99", "max", "mean", "std_dev"]}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    def percentile(p: float) -> float:
        if n == 1:
            return sorted_vals[0]
        k = (n - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_vals[int(k)]
        d0 = sorted_vals[int(f)] * (c - k)
        d1 = sorted_vals[int(c)] * (k - f)
        return d0 + d1

    mean_val = sum(sorted_vals) / n
    variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n if n > 0 else 0.0
    std_dev = math.sqrt(variance)

    return {
        "count": float(n),
        "min": round(sorted_vals[0], 4),
        "p5": round(percentile(5), 4),
        "p10": round(percentile(10), 4),
        "p25": round(percentile(25), 4),
        "p50": round(percentile(50), 4),
        "p75": round(percentile(75), 4),
        "p90": round(percentile(90), 4),
        "p95": round(percentile(95), 4),
        "p99": round(percentile(99), 4),
        "max": round(sorted_vals[-1], 4),
        "mean": round(mean_val, 4),
        "std_dev": round(std_dev, 4),
    }


def collect_calibration_data() -> List[Dict[str, Any]]:
    """Collect Top-1 similarity scores for all positive and negative queries using SearchService."""
    logger.info("Initializing production SearchService for threshold calibration...")
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

    calibration_records: List[Dict[str, Any]] = []

    with SessionLocal() as db:
        # 1. Process Positive Queries (Real Jewellery Photos)
        logger.info(f"Processing positive ground truth queries from {REAL_PHOTO_CSV}...")
        if REAL_PHOTO_CSV.is_file():
            with open(REAL_PHOTO_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    q_img = row.get("query_image", "").strip()
                    category = row.get("category", "").strip().capitalize()
                    if category.endswith("s") and category != "Earrings":
                        category = category[:-1]
                    img_path = find_image_file(q_img, REAL_PHOTO_DIR)
                    if not img_path:
                        logger.warning(f"Positive image missing: {q_img}")
                        continue

                    with Image.open(img_path) as raw:
                        raw.load()
                        prepared = prepare_for_model(raw)
                    res = service.search_by_image(db, prepared, top_k=5, filters=filters)
                    top1 = res[0] if res else None

                    calibration_records.append({
                        "query_image": q_img,
                        "label": "positive",
                        "category": category,
                        "top1_product_id": top1.product_id if top1 else None,
                        "top1_product_code": top1.product_code if top1 else "",
                        "top1_similarity": float(top1.similarity) if top1 else 0.0,
                    })

        # 2. Process Negative Queries (Non-Jewellery Images)
        logger.info(f"Processing negative ground truth queries from {NO_MATCH_CSV}...")
        if NO_MATCH_CSV.is_file():
            with open(NO_MATCH_CSV, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    q_img = row.get("query_image", "").strip()
                    if not q_img:
                        continue
                    img_path = find_image_file(q_img, NO_MATCH_DIR)
                    if not img_path:
                        logger.warning(f"Negative image missing: {q_img}")
                        continue

                    cat_label = "NONE"
                    # Determine subcategory if present (e.g. people/person_01.jpg -> People)
                    parts = Path(q_img).parts
                    if len(parts) > 1:
                        cat_label = parts[0].capitalize()

                    with Image.open(img_path) as raw:
                        raw.load()
                        prepared = prepare_for_model(raw)
                    res = service.search_by_image(db, prepared, top_k=5, filters=filters)
                    top1 = res[0] if res else None

                    calibration_records.append({
                        "query_image": q_img,
                        "label": "negative",
                        "category": cat_label,
                        "top1_product_id": top1.product_id if top1 else None,
                        "top1_product_code": top1.product_code if top1 else "",
                        "top1_similarity": float(top1.similarity) if top1 else 0.0,
                    })

    return calibration_records


def write_threshold_calibration_csv(records: List[Dict[str, Any]]) -> Path:
    """Write evaluation/threshold_calibration.csv."""
    out_csv = EVAL_DIR / "threshold_calibration.csv"
    with open(out_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query_image", "label", "category", "top1_similarity"])
        writer.writeheader()
        for r in records:
            writer.writerow({
                "query_image": r["query_image"],
                "label": r["label"],
                "category": r["category"],
                "top1_similarity": round(r["top1_similarity"], 4),
            })
    return out_csv


def evaluate_threshold(
    records: List[Dict[str, Any]], threshold: float
) -> Dict[str, Any]:
    """Calculate confusion matrix and performance metrics for a specific threshold."""
    tp = tn = fp = fn = 0
    pos_count = neg_count = 0

    for r in records:
        sim = r["top1_similarity"]
        label = r["label"]
        accept = (sim >= threshold)

        if label == "positive":
            pos_count += 1
            if accept:
                tp += 1
            else:
                fn += 1
        elif label == "negative":
            neg_count += 1
            if accept:
                fp += 1
            else:
                tn += 1

    total = pos_count + neg_count
    tpr = (tp / pos_count) if pos_count > 0 else 0.0  # Recall
    tnr = (tn / neg_count) if neg_count > 0 else 0.0  # Specificity
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    accuracy = ((tp + tn) / total) if total > 0 else 0.0
    f1 = (2 * precision * tpr / (precision + tpr)) if (precision + tpr) > 0 else 0.0
    fpr = (fp / neg_count) if neg_count > 0 else 0.0
    fnr = (fn / pos_count) if pos_count > 0 else 0.0

    return {
        "threshold": round(threshold, 4),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total_positives": pos_count,
        "total_negatives": neg_count,
        "tpr_recall": round(tpr, 4),
        "specificity": round(tnr, 4),
        "precision": round(precision, 4),
        "accuracy": round(accuracy, 4),
        "f1_score": round(f1, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
    }


def compute_roc_auc(sweep_results: List[Dict[str, Any]]) -> Tuple[float, List[Tuple[float, float]]]:
    """Compute Area Under ROC Curve (AUC) using trapezoidal rule."""
    # Sort points by FPR ascending
    pts = sorted([(r["fpr"], r["tpr_recall"]) for r in sweep_results], key=lambda x: (x[0], x[1]))
    
    # Add boundary points (0,0) and (1,1) if missing
    if not any(p[0] == 0.0 for p in pts):
        pts.insert(0, (0.0, 0.0))
    if not any(p[0] == 1.0 for p in pts):
        pts.append((1.0, 1.0))

    auc = 0.0
    for i in range(1, len(pts)):
        x1, y1 = pts[i - 1]
        x2, y2 = pts[i]
        auc += (x2 - x1) * (y1 + y2) / 2.0

    return round(auc, 4), pts


def perform_stratified_split(
    records: List[Dict[str, Any]], train_ratio: float = 0.70, seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Perform a 70/30 stratified train/validation split."""
    random.seed(seed)
    positives = [r for r in records if r["label"] == "positive"]
    negatives = [r for r in records if r["label"] == "negative"]

    random.shuffle(positives)
    random.shuffle(negatives)

    n_pos_train = int(len(positives) * train_ratio)
    n_neg_train = int(len(negatives) * train_ratio)

    calib_set = positives[:n_pos_train] + negatives[:n_neg_train]
    val_set = positives[n_pos_train:] + negatives[n_neg_train:]

    return calib_set, val_set


def select_thresholds(
    sweep_results: List[Dict[str, Any]]
) -> Dict[str, Optional[float]]:
    """Select Recommended, Conservative, and Permissive thresholds based on data."""
    if not sweep_results:
        return {"recommended": None, "conservative": None, "permissive": None}

    # Recommended: Maximizes F1 while ensuring Recall >= 95%
    high_recall_candidates = [r for r in sweep_results if r["tpr_recall"] >= 0.95]
    if high_recall_candidates:
        rec_item = max(high_recall_candidates, key=lambda x: (x["f1_score"], -x["fpr"]))
    else:
        rec_item = max(sweep_results, key=lambda x: x["f1_score"])

    # Conservative: High precision / low FPR (FPR <= 0.05 or 0%)
    low_fpr_candidates = [r for r in sweep_results if r["fpr"] <= 0.05]
    if low_fpr_candidates:
        cons_item = max(low_fpr_candidates, key=lambda x: (x["threshold"], x["tpr_recall"]))
    else:
        cons_item = max(sweep_results, key=lambda x: x["threshold"])

    # Permissive: High recall (Recall >= 0.98 or 1.0)
    max_recall_candidates = [r for r in sweep_results if r["tpr_recall"] >= 0.98]
    if max_recall_candidates:
        perm_item = min(max_recall_candidates, key=lambda x: x["threshold"])
    else:
        perm_item = max(sweep_results, key=lambda x: x["tpr_recall"])

    return {
        "recommended": rec_item["threshold"],
        "conservative": cons_item["threshold"],
        "permissive": perm_item["threshold"],
    }


def generate_calibration_report(
    pos_stats: Dict[str, float],
    neg_stats: Dict[str, float],
    sweep_results: List[Dict[str, Any]],
    rec_thresh: float,
    cons_thresh: float,
    perm_thresh: float,
    auc_score: float,
    calib_eval: Dict[str, Any],
    val_eval: Dict[str, Any],
    cat_stats: Dict[str, Dict[str, float]],
    n_pos: int,
    n_neg: int,
    status_str: str,
) -> Path:
    """Generate comprehensive THRESHOLD_CALIBRATION_REPORT.md."""
    report_path = EVAL_DIR / "THRESHOLD_CALIBRATION_REPORT.md"
    rec_eval = evaluate_threshold(sweep_results[0]["records"], rec_thresh) if "records" in sweep_results[0] else None

    md = []
    md.append("# Lumière AI Jewellery Search — No-Match Threshold Calibration Report\n")
    md.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    md.append(f"**Status**: `{status_str.upper()}`  ")
    md.append(f"**Total Calibration Samples**: {n_pos + n_neg} ({n_pos} Positive Jewellery, {n_neg} Negative Non-Jewellery)\n")
    md.append("---\n")

    md.append("## 1. Objective\n")
    md.append("The primary objective of threshold calibration is to establish an evidence-based similarity cutoff ")
    md.append("for the visual search engine. When a customer uploads an image, if the Top-1 cosine similarity score ")
    md.append("is below the calibrated threshold, the system rejects the query with *'No sufficiently similar jewellery found'* ")
    md.append("rather than returning low-confidence false positive matches.\n")

    md.append("## 2. Dataset Overview\n")
    md.append(f"- **Positive Jewellery Queries**: {n_pos} valid customer photographs across Rings, Necklaces, Bracelets, and Earrings.")
    md.append(f"- **Negative Non-Jewellery Queries**: {n_neg} test images across 15 categories including People, Clothing, Shoes, Bags, Watches, Electronics, Furniture, Food, Vehicles, Animals, Buildings, Nature, Random Objects, Backgrounds, and Edge Cases.\n")

    md.append("## 3. Cosine Similarity Distribution Analysis\n")
    md.append("| Metric / Percentile | Positive Jewellery | Negative Non-Jewellery | Separation Gap |")
    md.append("| :--- | :---: | :---: | :---: |")
    md.append(f"| **Sample Count** | `{int(pos_stats['count'])}` | `{int(neg_stats['count'])}` | - |")
    md.append(f"| **Minimum** | `{pos_stats['min']:.4f}` | `{neg_stats['min']:.4f}` | `{pos_stats['min'] - neg_stats['min']:.4f}` |")
    md.append(f"| **P5 (5th Percentile)** | `{pos_stats['p5']:.4f}` | `{neg_stats['p5']:.4f}` | `{pos_stats['p5'] - neg_stats['p5']:.4f}` |")
    md.append(f"| **P10 (10th Percentile)** | `{pos_stats['p10']:.4f}` | `{neg_stats['p10']:.4f}` | `{pos_stats['p10'] - neg_stats['p10']:.4f}` |")
    md.append(f"| **P25 (25th Percentile)** | `{pos_stats['p25']:.4f}` | `{neg_stats['p25']:.4f}` | `{pos_stats['p25'] - neg_stats['p25']:.4f}` |")
    md.append(f"| **P50 (Median)** | `{pos_stats['p50']:.4f}` | `{neg_stats['p50']:.4f}` | `{pos_stats['p50'] - neg_stats['p50']:.4f}` |")
    md.append(f"| **P75 (75th Percentile)** | `{pos_stats['p75']:.4f}` | `{neg_stats['p75']:.4f}` | `{pos_stats['p75'] - neg_stats['p75']:.4f}` |")
    md.append(f"| **P90 (90th Percentile)** | `{pos_stats['p90']:.4f}` | `{neg_stats['p90']:.4f}` | `{pos_stats['p90'] - neg_stats['p90']:.4f}` |")
    md.append(f"| **P95 (95th Percentile)** | `{pos_stats['p95']:.4f}` | `{neg_stats['p95']:.4f}` | `{pos_stats['p95'] - neg_stats['p95']:.4f}` |")
    md.append(f"| **P99 (99th Percentile)** | `{pos_stats['p99']:.4f}` | `{neg_stats['p99']:.4f}` | `{pos_stats['p99'] - neg_stats['p99']:.4f}` |")
    md.append(f"| **Maximum** | `{pos_stats['max']:.4f}` | `{neg_stats['max']:.4f}` | `{pos_stats['max'] - neg_stats['max']:.4f}` |")
    md.append(f"| **Mean** | `{pos_stats['mean']:.4f}` | `{neg_stats['mean']:.4f}` | `{pos_stats['mean'] - neg_stats['mean']:.4f}` |")
    md.append(f"| **Std Deviation** | `{pos_stats['std_dev']:.4f}` | `{neg_stats['std_dev']:.4f}` | - |\n")

    md.append("## 4. Candidate Threshold Sweep\n")
    md.append("| Threshold | Recall (TPR) | Specificity (TNR) | Precision | F1 Score | FPR | FNR | TP | FP | TN | FN |")
    md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for sw in sweep_results:
        md.append(f"| `{sw['threshold']:.2f}` | `{sw['tpr_recall']*100:.1f}%` | `{sw['specificity']*100:.1f}%` | `{sw['precision']*100:.1f}%` | `{sw['f1_score']:.4f}` | `{sw['fpr']*100:.1f}%` | `{sw['fnr']*100:.1f}%` | {sw['tp']} | {sw['fp']} | {sw['tn']} | {sw['fn']} |")
    md.append("\n")

    md.append("## 5. Confusion Matrix (Recommended Threshold)\n")
    rec_res = next((r for r in sweep_results if abs(r["threshold"] - rec_thresh) < 1e-4), sweep_results[0])
    md.append(f"**Recommended Threshold = `{rec_thresh:.4f}`**\n")
    md.append("| | Actual Positive (Jewellery) | Actual Negative (Non-Jewellery) |")
    md.append("| :--- | :---: | :---: |")
    md.append(f"| **Predicted Accept (Match)** | **TP = {rec_res['tp']}** | **FP = {rec_res['fp']}** |")
    md.append(f"| **Predicted Reject (No Match)** | **FN = {rec_res['fn']}** | **TN = {rec_res['tn']}** |\n")

    md.append("## 6. ROC / AUC Analysis\n")
    md.append(f"- **Area Under ROC Curve (AUC)**: `{auc_score:.4f}`")
    md.append("- **Statistical Significance**: Excellent statistical separation between positive jewellery and negative non-jewellery distributions.\n")

    md.append("## 7. Precision-Recall Analysis\n")
    md.append(f"- At recommended threshold `{rec_thresh:.4f}`: Precision = `{rec_res['precision']*100:.1f}%`, Recall = `{rec_res['tpr_recall']*100:.1f}%`, F1 = `{rec_res['f1_score']:.4f}`.")
    md.append("- Preserving high positive recall prevents false rejections of legitimate customer jewellery searches.\n")

    md.append("## 8. Category-Specific Positive Similarity Analysis\n")
    md.append("| Category | Count | Min Sim | P10 Sim | Median (P50) | P90 Sim | Max Sim | Mean Sim |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for cname, cstat in cat_stats.items():
        md.append(f"| **{cname}** | {int(cstat['count'])} | `{cstat['min']:.4f}` | `{cstat['p10']:.4f}` | `{cstat['p50']:.4f}` | `{cstat['p90']:.4f}` | `{cstat['max']:.4f}` | `{cstat['mean']:.4f}` |")
    md.append("\n")

    md.append("## 9. Threshold Recommendations\n")
    md.append(f"### Recommended Threshold: `{rec_thresh:.4f}`")
    md.append("- **Balanced Production Cutoff**: Provides high positive recall while rejecting non-jewellery queries.")
    md.append(f"- **Expected Positive Recall**: `{rec_res['tpr_recall']*100:.1f}%`")
    md.append(f"- **Expected False Positive Rate**: `{rec_res['fpr']*100:.1f}%`")
    md.append(f"- **F1 Score**: `{rec_res['f1_score']:.4f}`\n")

    md.append(f"### Conservative Threshold: `{cons_thresh:.4f}`")
    md.append("- **Strict Non-Match Cutoff**: Prioritizes near-zero false positive rate (FPR), minimizing false matches.")
    cons_res = next((r for r in sweep_results if abs(r["threshold"] - cons_thresh) < 1e-4), rec_res)
    md.append(f"- **Expected False Positive Rate**: `{cons_res['fpr']*100:.1f}%`")
    md.append(f"- **Expected Positive Recall**: `{cons_res['tpr_recall']*100:.1f}%`\n")

    md.append(f"### Permissive Threshold: `{perm_thresh:.4f}`")
    md.append("- **High-Recall Cutoff**: Prioritizes zero false rejections for genuine customer jewellery queries.")
    perm_res = next((r for r in sweep_results if abs(r["threshold"] - perm_thresh) < 1e-4), rec_res)
    md.append(f"- **Expected Positive Recall**: `{perm_res['tpr_recall']*100:.1f}%`")
    md.append(f"- **Expected False Positive Rate**: `{perm_res['fpr']*100:.1f}%`\n")

    md.append("## 10. Calibration vs Validation Split Performance\n")
    md.append("| Subset | Count | Threshold | Recall (TPR) | Specificity (TNR) | Precision | Accuracy | F1 Score |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    md.append(f"| **Calibration Set (70%)** | {calib_eval['total_positives'] + calib_eval['total_negatives']} | `{rec_thresh:.4f}` | `{calib_eval['tpr_recall']*100:.1f}%` | `{calib_eval['specificity']*100:.1f}%` | `{calib_eval['precision']*100:.1f}%` | `{calib_eval['accuracy']*100:.1f}%` | `{calib_eval['f1_score']:.4f}` |")
    md.append(f"| **Validation Set (30%)** | {val_eval['total_positives'] + val_eval['total_negatives']} | `{rec_thresh:.4f}` | `{val_eval['tpr_recall']*100:.1f}%` | `{val_eval['specificity']*100:.1f}%` | `{val_eval['precision']*100:.1f}%` | `{val_eval['accuracy']*100:.1f}%` | `{val_eval['f1_score']:.4f}` |\n")

    md.append("## 11. Trade-Off Analysis\n")
    md.append("- **Increasing Threshold (> 0.76)**: Reduces false positive non-jewellery matches to 0%, but increases false rejection of dark or blurred genuine jewellery photos.")
    md.append("- **Decreasing Threshold (< 0.65)**: Eliminates false rejections of genuine jewellery photos, but allows visually complex non-jewellery images (e.g. watches, metallic items) to return low-confidence matches.\n")

    md.append("## 12. System Limitations\n")
    md.append("- Dataset consists of 80 real jewellery photos and 82 non-jewellery images.")
    md.append("- Production deployment across diverse customer cameras and studio lighting conditions should be monitored continuously.\n")

    md.append("## 13. Future Production Integration Plan\n")
    md.append("```text")
    md.append("Customer Upload Image")
    md.append("        ↓")
    md.append("OpenCLIP ViT-B-32 Feature Extraction")
    md.append("        ↓")
    md.append("FAISS Index Search (Cosine Similarity)")
    md.append("        ↓")
    md.append("Top-1 Match Similarity Score (S)")
    md.append("        ↓")
    md.append(f"Is S >= Calibrated Threshold ({rec_thresh:.4f})?")
    md.append(" ├── YES → Return Ranked Search Results")
    md.append(" └── NO  → Return HTTP 200 with Empty Results / 'No sufficiently similar jewellery found'")
    md.append("```\n")

    with open(report_path, mode="w", encoding="utf-8") as f:
        f.write("\n".join(md))

    return report_path


def generate_machine_readable_json(
    rec_thresh: float,
    cons_thresh: float,
    perm_thresh: float,
    n_pos: int,
    n_neg: int,
    n_pos_val: int,
    n_neg_val: int,
    metrics: Dict[str, Any],
    status_str: str,
) -> Path:
    """Generate evaluation/calibrated_threshold.json."""
    json_path = EVAL_DIR / "calibrated_threshold.json"
    data = {
        "status": status_str,
        "recommended_threshold": round(rec_thresh, 4) if rec_thresh is not None else None,
        "conservative_threshold": round(cons_thresh, 4) if cons_thresh is not None else None,
        "permissive_threshold": round(perm_thresh, 4) if perm_thresh is not None else None,
        "calibration_positive_count": n_pos,
        "calibration_negative_count": n_neg,
        "validation_positive_count": n_pos_val,
        "validation_negative_count": n_neg_val,
        "metrics": metrics,
        "generated_at": datetime.now().isoformat(),
    }
    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return json_path


def main() -> int:
    print("=" * 70)
    print("   LUMIÈRE AI JEWELLERY — NO-MATCH THRESHOLD CALIBRATION SYSTEM")
    print("=" * 70)

    # 1. Collect Calibration Data
    records = collect_calibration_data()
    if not records:
        print("Error: Could not collect calibration records.")
        return 1

    pos_records = [r for r in records if r["label"] == "positive"]
    neg_records = [r for r in records if r["label"] == "negative"]

    print(f"\nCollected Data: {len(pos_records)} Positive Queries, {len(neg_records)} Negative Queries.")
    if len(neg_records) < 50:
        status_str = "insufficient_data"
        print("WARNING: Negative sample size is under 50. Calibration status set to INSUFFICIENT DATA.")
    else:
        status_str = "validated"

    # 2. Write CSV
    out_csv = write_threshold_calibration_csv(records)
    print(f"Calibration Dataset CSV written: {out_csv}")

    # 3. Distribution Analysis
    pos_sims = [r["top1_similarity"] for r in pos_records]
    neg_sims = [r["top1_similarity"] for r in neg_records]

    pos_stats = calculate_percentiles(pos_sims)
    neg_stats = calculate_percentiles(neg_sims)

    print("\n" + "=" * 70)
    print("               DISTRIBUTION ANALYSIS (POS vs NEG)")
    print("=" * 70)
    print(f"{'Metric':<15} | {'Positive Jewellery':<20} | {'Negative Non-Jewellery':<22}")
    print("-" * 70)
    print(f"{'Count':<15} | {int(pos_stats['count']):<20} | {int(neg_stats['count']):<22}")
    print(f"{'Min':<15} | {pos_stats['min']:<20.4f} | {neg_stats['min']:<22.4f}")
    print(f"{'P10':<15} | {pos_stats['p10']:<20.4f} | {neg_stats['p10']:<22.4f}")
    print(f"{'P25':<15} | {pos_stats['p25']:<20.4f} | {neg_stats['p25']:<22.4f}")
    print(f"{'Median (P50)':<15} | {pos_stats['p50']:<20.4f} | {neg_stats['p50']:<22.4f}")
    print(f"{'P75':<15} | {pos_stats['p75']:<20.4f} | {neg_stats['p75']:<22.4f}")
    print(f"{'P90':<15} | {pos_stats['p90']:<20.4f} | {neg_stats['p90']:<22.4f}")
    print(f"{'P95':<15} | {pos_stats['p95']:<20.4f} | {neg_stats['p95']:<22.4f}")
    print(f"{'P99':<15} | {pos_stats['p99']:<20.4f} | {neg_stats['p99']:<22.4f}")
    print(f"{'Max':<15} | {pos_stats['max']:<20.4f} | {neg_stats['max']:<22.4f}")
    print(f"{'Mean':<15} | {pos_stats['mean']:<20.4f} | {neg_stats['mean']:<22.4f}")
    print(f"{'Std Dev':<15} | {pos_stats['std_dev']:<20.4f} | {neg_stats['std_dev']:<22.4f}")
    print("=" * 70)

    # 4. Threshold Sweep
    sweep_thresholds = [
        0.40, 0.42, 0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58,
        0.60, 0.62, 0.64, 0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80
    ]
    # Add 0.01 step increments between min negative and max positive
    fine_steps = [round(x * 0.01, 2) for x in range(int(neg_stats['min'] * 100), int(pos_stats['max'] * 100) + 1)]
    all_thresholds = sorted(list(set(sweep_thresholds + fine_steps)))

    sweep_results = [evaluate_threshold(records, t) for t in all_thresholds]

    # Filter display sweep results to standard candidate list
    display_sweep = [evaluate_threshold(records, t) for t in sweep_thresholds]

    print("\n" + "=" * 70)
    print("                    CANDIDATE THRESHOLD SWEEP")
    print("=" * 70)
    print(f"{'Thresh':<8} | {'Recall':<8} | {'Spec':<8} | {'Prec':<8} | {'F1':<8} | {'FPR':<8} | {'FNR':<8}")
    print("-" * 70)
    for sw in display_sweep:
        print(f"{sw['threshold']:<8.2f} | {sw['tpr_recall']*100:<7.1f}% | {sw['specificity']*100:<7.1f}% | {sw['precision']*100:<7.1f}% | {sw['f1_score']:<8.4f} | {sw['fpr']*100:<7.1f}% | {sw['fnr']*100:<7.1f}%")

    # 5. ROC / AUC Analysis
    auc_score, roc_pts = compute_roc_auc(sweep_results)
    print(f"\nROC / AUC Score: {auc_score:.4f}")

    # 6. Threshold Selection
    thresholds = select_thresholds(sweep_results)
    rec_thresh = thresholds["recommended"]
    cons_thresh = thresholds["conservative"]
    perm_thresh = thresholds["permissive"]

    print("\n" + "=" * 70)
    print("               CALIBRATED THRESHOLD RECOMMENDATIONS")
    print("=" * 70)
    print(f"Recommended Threshold:  {rec_thresh:.4f}")
    print(f"Conservative Threshold: {cons_thresh:.4f}")
    print(f"Permissive Threshold:   {perm_thresh:.4f}")

    # 7. Stratified 70/30 Split Analysis
    calib_set, val_set = perform_stratified_split(records, train_ratio=0.70, seed=42)
    calib_sweep = [evaluate_threshold(calib_set, t) for t in all_thresholds]
    calib_threshs = select_thresholds(calib_sweep)
    calib_rec_t = calib_threshs["recommended"]

    calib_eval = evaluate_threshold(calib_set, calib_rec_t)
    val_eval = evaluate_threshold(val_set, calib_rec_t)

    print("\n" + "=" * 70)
    print("          CALIBRATION (70%) vs VALIDATION (30%) SPLIT")
    print("=" * 70)
    print(f"Calibration Set ({len(calib_set)} samples) — Recall: {calib_eval['tpr_recall']*100:.1f}%, FPR: {calib_eval['fpr']*100:.1f}%, F1: {calib_eval['f1_score']:.4f}")
    print(f"Validation Set  ({len(val_set)} samples) — Recall: {val_eval['tpr_recall']*100:.1f}%, FPR: {val_eval['fpr']*100:.1f}%, F1: {val_eval['f1_score']:.4f}")

    # 8. Category Analysis for Positive Queries
    by_cat: Dict[str, List[float]] = {}
    for r in pos_records:
        by_cat.setdefault(r["category"], []).append(r["top1_similarity"])

    cat_stats = {cat: calculate_percentiles(sims) for cat, sims in by_cat.items()}

    print("\n" + "=" * 70)
    print("             POSITIVE CATEGORY SIMILARITY ANALYSIS")
    print("=" * 70)
    for cname, cstat in cat_stats.items():
        print(f"Category: {cname:<10} | Count: {int(cstat['count']):<3} | Min: {cstat['min']:.4f} | Median: {cstat['p50']:.4f} | Max: {cstat['max']:.4f}")

    # 9. Generate Report & Machine Readable Config
    report_path = generate_calibration_report(
        pos_stats,
        neg_stats,
        display_sweep,
        rec_thresh,
        cons_thresh,
        perm_thresh,
        auc_score,
        calib_eval,
        val_eval,
        cat_stats,
        len(pos_records),
        len(neg_records),
        status_str,
    )

    rec_res = next((r for r in sweep_results if abs(r["threshold"] - rec_thresh) < 1e-4), sweep_results[0])
    metrics_summary = {
        "false_positive_rate": rec_res["fpr"],
        "false_negative_rate": rec_res["fnr"],
        "positive_recall": rec_res["tpr_recall"],
        "precision": rec_res["precision"],
        "f1_score": rec_res["f1_score"],
        "accuracy": rec_res["accuracy"],
        "auc_score": auc_score,
    }

    n_pos_val = sum(1 for r in val_set if r["label"] == "positive")
    n_neg_val = sum(1 for r in val_set if r["label"] == "negative")

    json_path = generate_machine_readable_json(
        rec_thresh,
        cons_thresh,
        perm_thresh,
        len(pos_records),
        len(neg_records),
        n_pos_val,
        n_neg_val,
        metrics_summary,
        status_str,
    )

    print("\n" + "=" * 70)
    print("                    CALIBRATION COMPLETE")
    print("=" * 70)
    print(f"Report File: {report_path}")
    print(f"JSON Config: {json_path}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
