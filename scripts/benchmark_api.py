from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request


def post_json(url: str, payload: dict, token: str = "") -> tuple[int, float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
            status = resp.status
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
    return status, (time.perf_counter() - t0) * 1000


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(int(len(ordered) * p), len(ordered) - 1)
    return round(ordered[idx], 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Small local benchmark for the IM Guard API /judge endpoint.")
    parser.add_argument("--url", default="http://127.0.0.1:8000/judge")
    parser.add_argument("--requests", type=int, default=50)
    parser.add_argument("--token", default="")
    args = parser.parse_args()
    payload = {
        "ticket_id": "bench-local",
        "chat_evidence_list": ["加微信稳赚，带你投资。"],
        "behavior_abnormal_list": ["短时间高频私聊。"],
    }
    latencies: list[float] = []
    status_counts: dict[int, int] = {}
    started = time.perf_counter()
    for i in range(args.requests):
        payload["ticket_id"] = f"bench-local-{i:05d}"
        status, latency = post_json(args.url, payload, args.token)
        latencies.append(latency)
        status_counts[status] = status_counts.get(status, 0) + 1
    elapsed = time.perf_counter() - started
    result = {
        "requests": args.requests,
        "elapsed_seconds": round(elapsed, 3),
        "qps": round(args.requests / elapsed, 2) if elapsed > 0 else 0,
        "status_counts": status_counts,
        "latency_ms": {
            "avg": round(statistics.mean(latencies), 2) if latencies else 0,
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
