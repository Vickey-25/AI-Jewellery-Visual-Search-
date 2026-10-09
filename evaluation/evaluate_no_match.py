"""No-Match / Non-Jewellery Evaluation System for Lumière AI Visual Search.

Evaluates non-jewellery query images (e.g. car, shoe, phone, tree) to measure
the observed top-1 similarity score distribution for threshold calibration.

Usage:
  python evaluation/evaluate_no_match.py
"""

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

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
logger = logging.getLogger("evaluate_no_match")

EVAL_DIR = BASE_DIR / "evaluation"
DEFAULT_CSV_PATH = EVAL_DIR / "no_match_ground_truth.csv"
DEFAULT_NO_MATCH_DIR = EVAL_DIR / "no_match"


def find_no_match_image(query_filename: str, no_match_dir: Path) -> Path | None:
    """Locate non-jewellery query image file."""
    candidates = [
        no_match_dir / query_filename,
        no_match_dir / Path(query_filename).name,
        EVAL_DIR / Path(query_filename),
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def run_no_match_evaluation(csv_path: Path, no_match_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Execute evaluation on non-jewellery test images."""
    if not csv_path.is_file():
        logger.error(f"No-match ground truth CSV not found: {csv_path}")
        return [], {}

    rows_to_process = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for line_num, r in enumerate(reader, start=2):
            q_img = r.get("query_image", "").strip()
            if not q_img:
                continue
            img_p = find_no_match_image(q_img, no_match_dir)
            if img_p:
                rows_to_process.append({"query_image": q_img, "img_path": img_p})
            else:
                logger.warning(f"Line {line_num}: No-match image file missing: '{q_img}'")

    if not rows_to_process:
        logger.error("No valid non-jewellery image files found.")
        return [], {}

    logger.info("Initializing SearchService for No-Match evaluation...")
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

    results = []
    with SessionLocal() as db:
        for item in rows_to_process:
            img_p: Path = item["img_path"]

            t0 = time.perf_counter()
            with Image.open(img_p) as raw:
                raw.load()
                prepared = prepare_for_model(raw)
            res_items = service.search_by_image(db, prepared, top_k=5, filters=filters)
            t1 = time.perf_counter()
            latency_ms = (t1 - t0) * 1000.0

            top1 = res_items[0] if res_items else None
            results.append({
                "query_image": item["query_image"],
                "expected_match": "NONE",
                "top1_product_id": top1.product_id if top1 else None,
                "top1_product_code": top1.product_code if top1 else "",
                "top1_category": top1.category if top1 else "",
                "top1_similarity": top1.similarity if top1 else 0.0,
                "latency_ms": latency_ms,
            })

    sims = [r["top1_similarity"] for r in results]
    sims_sorted = sorted(sims)
    n = len(sims)

    avg_sim = sum(sims) / n
    p50_sim = sims_sorted[int(n * 0.50)]
    p95_sim = sims_sorted[int(n * 0.95)] if n >= 5 else sims_sorted[-1]
    min_sim = sims_sorted[0]
    max_sim = sims_sorted[-1]

    latencies = [r["latency_ms"] for r in results]
    avg_lat = sum(latencies) / n

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_no_match_queries": n,
        "observed_similarity_distribution": {
            "average_top1_similarity": round(avg_sim, 4),
            "p50_top1_similarity": round(p50_sim, 4),
            "p95_top1_similarity": round(p95_sim, 4),
            "min_top1_similarity": round(min_sim, 4),
            "max_top1_similarity": round(max_sim, 4),
        },
        "average_latency_ms": round(avg_lat, 2),
        "false_match_analysis": {
            "status": "Threshold calibration required. Observed similarity distribution is provided for analysis.",
            "note": "The current system does not enforce a hard no-match cutoff threshold. Setting a cutoff (e.g., sim < 0.60) will prevent non-jewellery queries from returning matches.",
        },
    }

    return results, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate non-jewellery query images for no-match threshold calibration.")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV_PATH, help="Path to no-match CSV")
    parser.add_argument("--no-match-dir", type=Path, default=DEFAULT_NO_MATCH_DIR, help="Path to no-match directory")
    args = parser.parse_args()

    print("=" * 60)
    print("      LUMIÈRE NO-MATCH EVALUATION SYSTEM")
    print("=" * 60)
    print(f"No-Match CSV: {args.csv}")
    print(f"No-Match Dir: {args.no_match_dir}")

    results, summary = run_no_match_evaluation(args.csv, args.no_match_dir)
    if not results:
        print("No valid non-jewellery results generated.")
        return 1

    # Save outputs
    csv_out = EVAL_DIR / "no_match_results.csv"
    with open(csv_out, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "query_image",
                "expected_match",
                "top1_product_id",
                "top1_product_code",
                "top1_category",
                "top1_similarity",
                "latency_ms",
            ],
        )
        writer.writeheader()
        for r in results:
            row = dict(r)
            row["top1_similarity"] = round(row["top1_similarity"], 4)
            row["latency_ms"] = round(row["latency_ms"], 2)
            writer.writerow(row)

    json_out = EVAL_DIR / "no_match_summary.json"
    with open(json_out, mode="w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    sim_dist = summary["observed_similarity_distribution"]

    print("\n" + "=" * 60)
    print("               NO-MATCH EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Non-Jewellery Queries: {summary['total_no_match_queries']}")
    print(f"Average Top-1 Similarity:  {sim_dist['average_top1_similarity']}")
    print(f"P50 Top-1 Similarity:      {sim_dist['p50_top1_similarity']}")
    print(f"P95 Top-1 Similarity:      {sim_dist['p95_top1_similarity']}")
    print(f"Min / Max Top-1 Sim:       {sim_dist['min_top1_similarity']} / {sim_dist['max_top1_similarity']}")
    print(f"Average Latency:           {summary['average_latency_ms']} ms")
    print("-" * 60)
    print(f"Note: {summary['false_match_analysis']['status']}")
    print(f"CSV Output:  {csv_out}")
    print(f"JSON Output: {json_out}")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
