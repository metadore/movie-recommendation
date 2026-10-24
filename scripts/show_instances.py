#!/usr/bin/env python3
"""
show_instances.py
=================
Sends N sequential requests to /api/health and counts how many times each
backend instance responded.  Demonstrates round-robin load distribution.

Usage:
    python scripts/show_instances.py [--url http://localhost] [--n 30]
"""
import argparse
import json
import urllib.request
from collections import Counter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost")
    parser.add_argument("--n", type=int, default=30, help="Number of requests")
    args = parser.parse_args()

    endpoint = f"{args.url.rstrip('/')}/api/health"
    counts: Counter = Counter()
    errors = 0

    print(f"Sending {args.n} requests to {endpoint} …\n")
    for i in range(args.n):
        try:
            with urllib.request.urlopen(endpoint, timeout=5) as resp:
                data = json.loads(resp.read())
                instance = data.get("instance", "unknown")
                counts[instance] += 1
                print(f"  [{i+1:>3}] instance={instance}")
        except Exception as e:
            errors += 1
            print(f"  [{i+1:>3}] ERROR: {e}")

    print("\n── Distribution ─────────────────────────────")
    for inst, cnt in sorted(counts.items()):
        bar = "█" * cnt
        print(f"  {inst:<20} {cnt:>4}  {bar}")
    print(f"  Errors: {errors}")
    print("─────────────────────────────────────────────")


if __name__ == "__main__":
    main()
