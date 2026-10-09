"""Measure retrieval quality and performance latency on test queries.

Calculates:
- Recall@1, Recall@5, Recall@10
- Precision@1, Precision@5, Precision@10
- MRR (Mean Reciprocal Rank)
- Latency breakdown: Preprocessing, OpenCLIP Inference, FAISS Vector Search, DB Lookup, Total API Latency
"""
import csv
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set, Tuple, Any, Optional

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ai.clip_service import CLIPService
from app.ai.faiss_index import FaissIndex
from app.config import settings
from app.database.database import SessionLocal
from app.database.models import Product
from app.utils.image_utils import prepare_for_model

EVAL_DIR = Path(__file__).resolve().parent.parent.parent / "evaluation"
KS = (1, 5, 10)


def calculate_mrr(ranked_list: List[int], relevant_set: Set[int]) -> float:
    for rank_idx, item in enumerate(ranked_list, start=1):
        if item in relevant_set:
            return 1.0 / rank_idx
    return 0.0


def find_query_image(query_filename: str) -> Optional[Path]:
    candidates = [
        EVAL_DIR / "real_photos" / query_filename,
        EVAL_DIR / "queries" / Path(query_filename).name,
        EVAL_DIR / query_filename,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand
    return None


def main() -> int:
    gt_csv_path = EVAL_DIR / "real_photo_ground_truth.csv"
    expected_path = EVAL_DIR / "expected" / "expected.json"

    index = FaissIndex(settings.faiss_index_path, settings.faiss_mapping_path)
    if not index.load():
        print("FAISS index not found. Run scripts/create_index.py first.")
        return 1

    print("Loading OpenCLIP model for evaluation...")
    clip = CLIPService(settings.model_name, settings.model_pretrained,
                       settings.model_device, settings.torch_num_threads)

    with SessionLocal() as db:
        active_products = db.query(Product).filter(Product.is_active.is_(True)).all()
        code_by_id: Dict[int, str] = {p.id: p.product_code for p in active_products if p.product_code}

        # Build map of image content hash -> set of product IDs for duplicate resolution
        hash_to_ids: Dict[str, Set[int]] = {}
        for p in active_products:
            if p.image_filename:
                img_path = settings.images_dir / p.image_filename
                if img_path.is_file():
                    h = hashlib.md5(img_path.read_bytes()).hexdigest()
                    hash_to_ids.setdefault(h, set()).add(p.id)

    queries_to_eval: List[Dict[str, Any]] = []

    if gt_csv_path.is_file():
        with open(gt_csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                q_img = row.get("query_image", "").strip()
                exp_id_str = row.get("expected_product_id", "").strip()
                if not q_img or not exp_id_str.isdigit():
                    continue
                exp_id = int(exp_id_str)
                acc_ids: Set[int] = {exp_id}
                raw_acc = row.get("acceptable_product_ids", "").strip()
                if raw_acc:
                    for part in raw_acc.split("|"):
                        if part.strip().isdigit():
                            acc_ids.add(int(part.strip()))

                prod = next((p for p in active_products if p.id == exp_id), None)
                if prod and prod.image_filename:
                    img_path = settings.images_dir / prod.image_filename
                    if img_path.is_file():
                        h = hashlib.md5(img_path.read_bytes()).hexdigest()
                        acc_ids.update(hash_to_ids.get(h, set()))

                img_file = find_query_image(q_img)
                if img_file:
                    queries_to_eval.append({
                        "filename": q_img,
                        "img_path": img_file,
                        "expected_id": exp_id,
                        "acceptable_ids": acc_ids,
                    })
    elif expected_path.is_file():
        expected_data: Dict[str, List[str]] = json.loads(expected_path.read_text(encoding="utf-8"))
        code_to_id = {v: k for k, v in code_by_id.items()}
        for fname, relevant in expected_data.items():
            img_file = find_query_image(fname)
            if img_file and relevant:
                acc_ids = {code_to_id[c] for c in relevant if c in code_to_id}
                if acc_ids:
                    queries_to_eval.append({
                        "filename": fname,
                        "img_path": img_file,
                        "expected_id": list(acc_ids)[0],
                        "acceptable_ids": acc_ids,
                    })

    per_query: List[Dict[str, Any]] = []
    recalls = {k: 0.0 for k in KS}
    precisions = {k: 0.0 for k in KS}
    mrr_sum = 0.0

    latencies_prep: List[float] = []
    latencies_clip: List[float] = []
    latencies_faiss: List[float] = []
    latencies_db: List[float] = []
    latencies_total: List[float] = []

    clean_hits = {k: 0 for k in KS}
    clean_count = 0
    real_photo_hits = {k: 0 for k in KS}
    real_photo_count = 0

    for item in queries_to_eval:
        filename: str = item["filename"]
        path: Path = item["img_path"]
        acceptable_set: Set[int] = item["acceptable_ids"]

        t0 = time.perf_counter()
        with Image.open(path) as raw:
            raw.load()
            prep_img = prepare_for_model(raw)
        t1 = time.perf_counter()

        vec = clip.generate_image_embedding(prep_img)
        t2 = time.perf_counter()

        faiss_matches = index.search(vec, max(KS))
        t3 = time.perf_counter()

        ranked_ids: List[int] = [pid for pid, _ in faiss_matches]
        ranked_codes: List[str] = [code_by_id[pid] for pid in ranked_ids if pid in code_by_id]
        t4 = time.perf_counter()

        dt_prep = (t1 - t0) * 1000.0
        dt_clip = (t2 - t1) * 1000.0
        dt_faiss = (t3 - t2) * 1000.0
        dt_db = (t4 - t3) * 1000.0
        dt_total = (t4 - t0) * 1000.0

        latencies_prep.append(dt_prep)
        latencies_clip.append(dt_clip)
        latencies_faiss.append(dt_faiss)
        latencies_db.append(dt_db)
        latencies_total.append(dt_total)

        query_mrr = calculate_mrr(ranked_ids, acceptable_set)
        mrr_sum += query_mrr

        relevant_codes: List[str] = [code_by_id[pid] for pid in acceptable_set if pid in code_by_id]

        row: Dict[str, Any] = {
            "query": filename,
            "relevant": relevant_codes,
            "top_ranked": ranked_codes,
            "mrr": round(query_mrr, 4),
            "latency_ms": round(dt_total, 2)
        }

        is_clean = "clean" in filename
        if is_clean:
            clean_count += 1
        else:
            real_photo_count += 1

        for k in KS:
            has_hit = 1 if (set(ranked_ids[:k]) & acceptable_set) else 0
            rec = float(has_hit)
            prec = len(set(ranked_ids[:k]) & acceptable_set) / k
            row[f"recall@{k}"] = round(rec, 4)
            row[f"precision@{k}"] = round(prec, 4)

            recalls[k] += rec
            precisions[k] += prec

            if has_hit:
                if is_clean:
                    clean_hits[k] += 1
                else:
                    real_photo_hits[k] += 1

        per_query.append(row)

    n_queries = len(per_query)
    if n_queries == 0:
        print("No usable queries found.")
        return 1

    avg_recalls = {f"recall@{k}": round(recalls[k] / n_queries, 4) for k in KS}
    avg_precisions = {f"precision@{k}": round(precisions[k] / n_queries, 4) for k in KS}
    mean_mrr = round(mrr_sum / n_queries, 4)

    p50_latency = round(sorted(latencies_total)[int(n_queries * 0.50)], 2)
    p95_latency = round(sorted(latencies_total)[int(n_queries * 0.95)], 2)
    avg_prep = round(sum(latencies_prep) / n_queries, 2)
    avg_clip = round(sum(latencies_clip) / n_queries, 2)
    avg_faiss = round(sum(latencies_faiss) / n_queries, 2)
    avg_db = round(sum(latencies_db) / n_queries, 2)

    clean_benchmark: Dict[str, float] = {
        f"recall@{k}": round(clean_hits[k] / clean_count, 4) if clean_count else 0.0 for k in KS
    }
    real_photo_benchmark: Dict[str, float] = {
        f"recall@{k}": round(real_photo_hits[k] / real_photo_count, 4) if real_photo_count else 0.0 for k in KS
    }

    metrics: Dict[str, Any] = {
        **avg_recalls,
        **avg_precisions,
        "mrr": mean_mrr,
        "clean_benchmark": clean_benchmark,
        "real_photo_benchmark": real_photo_benchmark,
    }

    summary: Dict[str, Any] = {
        "total_queries": n_queries,
        "clean_queries": clean_count,
        "real_photo_queries": real_photo_count,
        "metrics": metrics,
        "latency_ms": {
            "preprocessing_avg": avg_prep,
            "clip_inference_avg": avg_clip,
            "faiss_search_avg": avg_faiss,
            "db_lookup_avg": avg_db,
            "p50_total": p50_latency,
            "p95_total": p95_latency,
        }
    }

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    out_file = results_dir / f"eval_{datetime.now():%Y%m%d_%H%M%S}.json"
    latest_file = results_dir / "latest_eval.json"

    json_content = json.dumps({"summary": summary, "per_query": per_query}, indent=2)
    out_file.write_text(json_content, encoding="utf-8")
    latest_file.write_text(json_content, encoding="utf-8")

    print("\n" + "=" * 60)
    print("      LUMIÈRE VISUAL SEARCH EVALUATION REPORT")
    print("=" * 60)
    print(f"Total Queries Evaluated: {n_queries} (Clean: {clean_count}, Real-Photo/Modified: {real_photo_count})")
    print("-" * 60)
    print("Overall Retrieval Accuracy:")
    print(f"  Recall@1:  {avg_recalls['recall@1'] * 100:.1f}%")
    print(f"  Recall@5:  {avg_recalls['recall@5'] * 100:.1f}%")
    print(f"  Recall@10: {avg_recalls['recall@10'] * 100:.1f}%")
    print(f"  MRR:       {mean_mrr:.4f}")
    print("-" * 60)
    print("Clean Catalog Benchmark vs Real Customer Photo Benchmark:")
    print(f"  Clean Catalog Queries    -> Recall@1: {clean_benchmark['recall@1']*100:.1f}% | Recall@5: {clean_benchmark['recall@5']*100:.1f}%")
    print(f"  Real Customer Photo Test -> Recall@1: {real_photo_benchmark['recall@1']*100:.1f}% | Recall@5: {real_photo_benchmark['recall@5']*100:.1f}%")
    print("-" * 60)
    print("Performance Latency Breakdown:")
    print(f"  Image Preprocessing:    {avg_prep:.2f} ms")
    print(f"  OpenCLIP Inference:     {avg_clip:.2f} ms")
    print(f"  FAISS Search:           {avg_faiss:.2f} ms")
    print(f"  DB Mapping:             {avg_db:.2f} ms")
    print(f"  P50 Total Latency:      {p50_latency:.2f} ms")
    print(f"  P95 Total Latency:      {p95_latency:.2f} ms")
    print("=" * 60)
    print(f"Detailed JSON output saved to: {latest_file}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
