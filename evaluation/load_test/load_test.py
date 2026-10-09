"""Production-Readiness Load and Concurrency Test Harness for Lumière Backend.

This test harness evaluates throughput, latency, API correctness, and system resource metrics
under varying concurrency levels. It isolates test-harness logic from production code.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import psutil

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("load_test")

# Paths
BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

JEWELLERY_IMAGE = Path("backend/data/images/hf_br_000001.jpeg").resolve()
NO_MATCH_IMAGE = Path("evaluation/no_match/car.jpg").resolve()


def get_system_snapshot() -> Dict[str, Any]:
    """Capture system-wide and uvicorn process metrics."""
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    
    uvicorn_procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'cpu_percent']):
        try:
            cmdline = " ".join(proc.info['cmdline'] or [])
            if "uvicorn" in cmdline or ("python" in proc.info['name'].lower() and "app.main:app" in cmdline):
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
                uvicorn_procs.append({
                    "pid": proc.info['pid'],
                    "mem_mb": round(mem_mb, 2),
                    "cpu_percent": proc.info['cpu_percent'] or 0.0,
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return {
        "system_cpu_percent": cpu_percent,
        "system_ram_percent": mem.percent,
        "system_ram_used_gb": round((mem.total - mem.available) / (1024**3), 2),
        "system_ram_total_gb": round(mem.total / (1024**3), 2),
        "uvicorn_processes": uvicorn_procs,
        "uvicorn_process_count": len(uvicorn_procs),
    }


async def send_single_request(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    image_bytes: bytes,
    filename: str,
    top_k: int = 5,
    is_no_match: bool = False,
    timeout_sec: float = 30.0,
) -> Dict[str, Any]:
    """Send a single visual-search request and record outcome & latency."""
    result = {
        "status_code": 0,
        "latency_ms": 0.0,
        "success": False,
        "error_type": None,
        "is_200": False,
        "is_4xx": False,
        "is_5xx": False,
        "is_timeout": False,
        "validation_passed": False,
        "top1_similarity": None,
        "results_count": 0,
    }
    
    files = {"image": (filename, image_bytes, "image/jpeg")}
    data = {"top_k": str(top_k)}

    async with semaphore:
        start_time = time.perf_counter()
        try:
            resp = await client.post(
                url,
                files=files,
                data=data,
                timeout=timeout_sec,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = elapsed_ms
            result["status_code"] = resp.status_code
            
            if resp.status_code == 200:
                result["is_200"] = True
                payload = resp.json()
                results_list = payload.get("results", [])
                result["results_count"] = len(results_list)

                if is_no_match:
                    # Expect results == [] and message == "No sufficiently similar jewellery found."
                    msg = payload.get("message", "")
                    if len(results_list) == 0 and msg == "No sufficiently similar jewellery found.":
                        result["validation_passed"] = True
                        result["success"] = True
                    else:
                        result["error_type"] = f"NoMatchMismatch(results={len(results_list)}, msg={msg})"
                else:
                    # Expect results > 0 and top1_similarity >= 0.80
                    if len(results_list) > 0:
                        top1_sim = results_list[0].get("similarity", 0.0)
                        result["top1_similarity"] = top1_sim
                        if top1_sim >= 0.80:
                            result["validation_passed"] = True
                            result["success"] = True
                        else:
                            result["error_type"] = f"LowSimilarity({top1_sim:.4f} < 0.80)"
                    else:
                        result["error_type"] = "UnexpectedEmptyResults"
            elif 400 <= resp.status_code < 500:
                result["is_4xx"] = True
                result["error_type"] = f"HTTP_{resp.status_code}"
            elif resp.status_code >= 500:
                result["is_5xx"] = True
                result["error_type"] = f"HTTP_{resp.status_code}"
        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = elapsed_ms
            result["is_timeout"] = True
            result["error_type"] = "Timeout"
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = elapsed_ms
            result["error_type"] = f"Exception_{type(exc).__name__}"

    return result


async def run_concurrency_level(
    target_url: str,
    concurrency: int,
    num_requests: int,
    image_path: Path,
    is_no_match: bool = False,
    top_k: int = 5,
    timeout_sec: float = 30.0,
) -> Dict[str, Any]:
    """Execute load test at specified concurrency level."""
    logger.info(
        "Starting test: Concurrency=%d, Requests=%d, Image=%s, NoMatch=%s",
        concurrency, num_requests, image_path.name, is_no_match
    )
    
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(
        max_connections=concurrency + 50,
        max_keepalive_connections=concurrency + 10,
    )
    
    # System monitoring snapshots
    sys_before = get_system_snapshot()
    sys_during_list = []

    async def monitor_task():
        while True:
            await asyncio.sleep(0.5)
            sys_during_list.append(get_system_snapshot())

    mon_handle = asyncio.create_task(monitor_task())

    wall_start = time.perf_counter()
    async with httpx.AsyncClient(limits=limits) as client:
        tasks = [
            send_single_request(
                client=client,
                semaphore=semaphore,
                url=target_url,
                image_bytes=image_bytes,
                filename=image_path.name,
                top_k=top_k,
                is_no_match=is_no_match,
                timeout_sec=timeout_sec,
            )
            for _ in range(num_requests)
        ]
        responses = await asyncio.gather(*tasks)
    wall_duration = time.perf_counter() - wall_start
    mon_handle.cancel()

    sys_after = get_system_snapshot()

    # Aggregate metrics
    latencies = [r["latency_ms"] for r in responses]
    success_count = sum(1 for r in responses if r["success"])
    failed_count = num_requests - success_count
    http_200_count = sum(1 for r in responses if r["is_200"])
    http_4xx_count = sum(1 for r in responses if r["is_4xx"])
    http_5xx_count = sum(1 for r in responses if r["is_5xx"])
    timeout_count = sum(1 for r in responses if r["is_timeout"])
    
    rps = num_requests / wall_duration if wall_duration > 0 else 0.0
    error_rate = (failed_count / num_requests) * 100.0

    avg_latency = float(np.mean(latencies)) if latencies else 0.0
    min_latency = float(np.min(latencies)) if latencies else 0.0
    max_latency = float(np.max(latencies)) if latencies else 0.0
    p50_latency = float(np.percentile(latencies, 50)) if latencies else 0.0
    p95_latency = float(np.percentile(latencies, 95)) if latencies else 0.0
    p99_latency = float(np.percentile(latencies, 99)) if latencies else 0.0

    # Average system usage during test run
    avg_cpu = float(np.mean([s["system_cpu_percent"] for s in sys_during_list])) if sys_during_list else sys_before["system_cpu_percent"]
    avg_ram = float(np.mean([s["system_ram_percent"] for s in sys_during_list])) if sys_during_list else sys_before["system_ram_percent"]

    result_summary = {
        "concurrency": concurrency,
        "total_requests": num_requests,
        "successful_requests": success_count,
        "failed_requests": failed_count,
        "http_200_count": http_200_count,
        "http_4xx_count": http_4xx_count,
        "http_5xx_count": http_5xx_count,
        "timeout_count": timeout_count,
        "error_rate_pct": round(error_rate, 2),
        "requests_per_sec": round(rps, 2),
        "wall_duration_sec": round(wall_duration, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "min_latency_ms": round(min_latency, 2),
        "max_latency_ms": round(max_latency, 2),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "p99_latency_ms": round(p99_latency, 2),
        "avg_cpu_percent": round(avg_cpu, 1),
        "avg_ram_percent": round(avg_ram, 1),
        "test_image": image_path.name,
        "is_no_match": is_no_match,
    }

    logger.info(
        "Completed C=%d: RPS=%.2f, Avg=%.1fms, P50=%.1fms, P95=%.1fms, Errors=%d/%d (%.1f%%)",
        concurrency, rps, avg_latency, p50_latency, p95_latency, failed_count, num_requests, error_rate
    )
    return result_summary


async def main():
    parser = argparse.ArgumentParser(description="Lumiere Backend Load Test")
    parser.add_argument("--url", default="http://127.0.0.1:8000/api/v1/search/image")
    parser.add_argument("--worker-config", default="1_worker")
    parser.add_argument("--skip-100", action="store_true", help="Skip concurrency 100 if unsafe")
    args = parser.parse_args()

    # Pre-test health check
    health_url = args.url.replace("/search/image", "/health")
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(health_url, timeout=5.0)
            if r.status_code != 200:
                logger.error("Backend health check failed: HTTP %d", r.status_code)
                sys.exit(1)
            logger.info("Backend health check OK: %s", r.json())
        except Exception as e:
            logger.error("Cannot connect to backend at %s: %s", health_url, e)
            sys.exit(1)

    # Standard concurrency levels & request counts for primary Jewellery Search
    jewellery_suite = [
        (1, 20),
        (10, 50),
        (25, 100),
        (50, 150),
    ]
    if not args.skip_100:
        jewellery_suite.append((100, 150))

    suite_results = []

    logger.info("=== STARTING JEWELLERY VISUAL SEARCH LOAD TEST (%s) ===", args.worker_config)
    for conc, n_req in jewellery_suite:
        res = await run_concurrency_level(
            target_url=args.url,
            concurrency=conc,
            num_requests=n_req,
            image_path=JEWELLERY_IMAGE,
            is_no_match=False,
        )
        suite_results.append(res)
        await asyncio.sleep(2.0)  # Cool down between runs

    logger.info("=== STARTING NO-MATCH CONCURRENCY TEST (%s) ===", args.worker_config)
    no_match_suite = [
        (10, 50),
        (25, 100),
    ]
    no_match_results = []
    for conc, n_req in no_match_suite:
        res = await run_concurrency_level(
            target_url=args.url,
            concurrency=conc,
            num_requests=n_req,
            image_path=NO_MATCH_IMAGE,
            is_no_match=True,
        )
        no_match_results.append(res)
        await asyncio.sleep(2.0)

    output_payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_config": args.worker_config,
        "target_url": args.url,
        "python_version": sys.version,
        "system_hardware": {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        },
        "jewellery_search_results": suite_results,
        "no_match_search_results": no_match_results,
    }

    out_file = RESULTS_DIR / f"load_test_results_{args.worker_config}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    logger.info("Saved load test results to %s", out_file)


if __name__ == "__main__":
    asyncio.run(main())
