"""Bounded loopback-only, read-only HTTP baseline. No Predict calls or ML claims."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import platform
import subprocess
from threading import Event, Thread
import time
from urllib.parse import urlsplit
from typing import Any

import httpx

ROUTES = ("/health/live", "/health/ready", "/api/v1/disease-info?limit=10",
          "/api/v1/predict/capabilities")


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * percent) - 1)]


def process_rss(pid: int) -> int | None:
    """Best-effort working set/RSS; missing permission is unknown, never zero."""
    if os.name == "nt":
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                 f"(Get-Process -Id {int(pid)} -ErrorAction Stop).WorkingSet64"],
                capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
            return int(result.stdout.strip()) if result.returncode == 0 else None
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return None
    try:
        for line in Path(f"/proc/{int(pid)}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError):
        pass
    return None


def run_baseline(base_url: str, *, requests: int, concurrency: int, timeout: float,
                 server_pid: int | None = None) -> dict[str, Any]:
    url = urlsplit(base_url)
    if (url.scheme != "http" or url.hostname not in {"127.0.0.1", "localhost", "::1"}
            or url.username or url.password or url.query or url.fragment or url.path not in {"", "/"}):
        raise ValueError("Use a local HTTP server root URL only; remote load tests are not authorized by this tool")
    if not 1 <= requests <= 5000 or not 1 <= concurrency <= 32 or not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError("Bounds: requests 1..5000, concurrency 1..32, timeout (0,60]")
    if server_pid is not None and server_pid <= 0:
        raise ValueError("server_pid must be positive")
    samples: list[int] = []
    stop = Event()

    def memory_sampler() -> None:
        while not stop.is_set():
            value = process_rss(server_pid) if server_pid is not None else None
            if value is not None:
                samples.append(value)
            stop.wait(0.5)

    sampler = Thread(target=memory_sampler, daemon=True)
    if server_pid is not None:
        sampler.start()
    try:
        with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout, follow_redirects=False,
                          trust_env=False, limits=httpx.Limits(max_connections=concurrency,
                                                            max_keepalive_connections=concurrency)) as client:
            warmup = [client.get(route).status_code for route in ROUTES]
            if any(code != 200 for code in warmup):
                raise ValueError("Warmup requires all four endpoints to return 200 (including schema readiness)")

            def one(index: int) -> dict[str, Any]:
                route = ROUTES[index % len(ROUTES)]
                started = time.perf_counter()
                try:
                    response = client.get(route)
                    result = str(response.status_code)
                except httpx.TimeoutException:
                    result = "timeout"
                except httpx.HTTPError:
                    result = "transport_error"
                return {"route": route, "result": result, "ms": (time.perf_counter() - started) * 1000}

            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                rows = list(pool.map(one, range(requests)))
            elapsed = time.perf_counter() - started
    finally:
        stop.set()
        if server_pid is not None:
            sampler.join(timeout=6)
    by_route = {}
    for route in ROUTES:
        selected = [row for row in rows if row["route"] == route]
        timings = [row["ms"] for row in selected]
        by_route[route] = {"attempts": len(selected), "results": dict(Counter(row["result"] for row in selected)),
                           "p50_ms": percentile(timings, 0.5), "p95_ms": percentile(timings, 0.95)}
    return {"scope": "loopback_read_only_http_no_inference", "base_url": base_url,
            "api_server_pid": server_pid, "client_os": platform.platform(),
            "client_machine": platform.machine(), "logical_cpu_count": os.cpu_count(),
            "python": platform.python_version(), "requests": requests, "concurrency": concurrency,
            "timeout_seconds": timeout, "warmup_requests_excluded": len(ROUTES),
            "elapsed_seconds": elapsed, "requests_per_second": requests / elapsed,
            "results": dict(Counter(row["result"] for row in rows)), "routes": by_route,
            "memory": {"method": "sampled_server_working_set_or_rss", "samples": len(samples),
                        "sampled_peak_bytes": max(samples) if samples else None},
            "limitations": ["Not a Predict/ML benchmark or production capacity estimate",
                            "Client and server share a machine; warmup excluded; samples are not exact peak RAM",
                            "No frontend/browser, reverse proxy or TLS evaluated"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--server-pid", type=int)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Report already exists; choose a new output file")
    try:
        result = run_baseline(args.base_url, requests=args.requests, concurrency=args.concurrency,
                              timeout=args.timeout, server_pid=args.server_pid)
    except (ValueError, httpx.HTTPError) as exc:
        raise SystemExit(f"Baseline not recorded: local server/readiness/configuration check failed ({type(exc).__name__})") from None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print("Read-only HTTP baseline recorded; no inference was executed")


if __name__ == "__main__":
    main()
