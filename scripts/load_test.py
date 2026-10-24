#!/usr/bin/env python3
"""
load_test.py – CinePulse load test runner
Uses the built-in `hey` wrapper or falls back to urllib for environments
where hey is not installed.

Usage:
    python load_test.py --url http://localhost/api/health --requests 1000 --concurrency 50
"""
import argparse
import subprocess
import sys
import time
import urllib.request
import threading
from dataclasses import dataclass


@dataclass
class Result:
    total_requests: int
    failed: int
    duration_secs: float
    rps: float
    avg_latency_ms: float


def run_with_hey(url: str, n: int, c: int) -> Result | None:
    """Try to run 'hey'. Return None if hey is not found."""
    try:
        start = time.perf_counter()
        out = subprocess.check_output(
            ["hey", "-n", str(n), "-c", str(c), url],
            stderr=subprocess.STDOUT,
            text=True,
        )
        elapsed = time.perf_counter() - start
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise

    # Parse hey output
    rps = 0.0
    avg_ms = 0.0
    failed = 0
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Requests/sec:"):
            rps = float(line.split()[-1])
        elif line.startswith("Average:"):
            avg_ms = float(line.split()[1]) * 1000
        elif "Non-2xx or 3xx responses:" in line:
            failed = int(line.split()[-1])
    print(out)
    return Result(n, failed, elapsed, rps, avg_ms)


def run_with_urllib(url: str, n: int, c: int) -> Result:
    """Pure-Python fallback load tester."""
    print(f"[urllib fallback] {n} requests, concurrency {c} -> {url}")
    results = {"ok": 0, "fail": 0, "total_ms": 0.0}
    lock = threading.Lock()
    sem = threading.Semaphore(c)

    def worker():
        sem.acquire()
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                _ = resp.read()
                ok = resp.status < 400
        except Exception:
            ok = False
        elapsed_ms = (time.perf_counter() - t0) * 1000
        with lock:
            if ok:
                results["ok"] += 1
            else:
                results["fail"] += 1
            results["total_ms"] += elapsed_ms
        sem.release()

    wall_start = time.perf_counter()
    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall_elapsed = time.perf_counter() - wall_start

    total = results["ok"] + results["fail"]
    avg_ms = results["total_ms"] / total if total else 0
    rps = total / wall_elapsed if wall_elapsed else 0
    print(
        f"  Done: {results['ok']} ok, {results['fail']} failed, "
        f"{rps:.1f} req/s, avg latency {avg_ms:.1f} ms"
    )
    return Result(total, results["fail"], wall_elapsed, rps, avg_ms)


def main():
    parser = argparse.ArgumentParser(description="CinePulse Load Tester")
    parser.add_argument("--url", default="http://localhost/api/health")
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=50)
    args = parser.parse_args()

    result = run_with_hey(args.url, args.requests, args.concurrency)
    if result is None:
        print("'hey' not found – using urllib fallback")
        result = run_with_urllib(args.url, args.requests, args.concurrency)

    print("\n===========================================")
    print(f"  Requests : {result.total_requests:<29}")
    print(f"  Failed   : {result.failed:<29}")
    print(f"  Duration : {result.duration_secs:<29.2f}")
    print(f"  Req/sec  : {result.rps:<29.2f}")
    print(f"  Avg ms   : {result.avg_latency_ms:<29.2f}")
    print("===========================================")



if __name__ == "__main__":
    main()
