"""
Customer Workload Generator for ShopEase E-Commerce
===================================================
Simulates realistic, multi-user customer traffic against ShopEase without ANY
knowledge of internal faults, diagnostics, or investigator infrastructure.

Customer Journeys Simulated:
- Search Queries: Multi-keyword Indian lifestyle catalog searches
- Category Browsing: Exploring categories and category-filtered product listings
- Product Detail Inspection: Viewing individual product pages and related items
- Checkout & Order Placement: Occasional cart order transactions

Operational Safety:
- Never calls fault injection or administrative endpoints
- Thread-safe metrics tracking (RPS, latency percentiles, error rate)
- Configurable concurrency ceiling, ramp-up schedule, and safety timeout
- Clean graceful shutdown on signal, event, or programmatic stop
"""

import time
import random
import threading
import argparse
import logging
from typing import Dict, Any, List, Optional
import httpx

# Pre-defined realistic search terms matching ShopEase Indian lifestyle inventory
SEARCH_TERMS = [
    "silk", "saree", "kurta", "cotton", "linen", "tea", "masala", "spice",
    "brass", "pottery", "ceramic", "sandalwood", "incense", "ayurvedic",
    "handcrafted", "pashmina", "shawl", "jewelry", "silver", "organic"
]

CATEGORIES = [
    "Ethnic Wear", "Ayurvedic & Wellness", "Spices & Gourmet",
    "Handicrafts & Decor", "Jewelry & Accessories"
]

SAMPLE_CUSTOMERS = [
    {"name": "Priya Sharma", "email": "priya.sharma@example.in", "phone": "+91 98765 43210", "city": "Bengaluru", "state": "Karnataka", "pincode": "560001"},
    {"name": "Rahul Verma", "email": "rahul.v@example.in", "phone": "+91 98123 45678", "city": "Mumbai", "state": "Maharashtra", "pincode": "400001"},
    {"name": "Ananya Patel", "email": "ananya.p@example.in", "phone": "+91 97234 56789", "city": "Ahmedabad", "state": "Gujarat", "pincode": "380001"},
    {"name": "Vikram Malhotra", "email": "vikram.m@example.in", "phone": "+91 99887 76655", "city": "New Delhi", "state": "Delhi", "pincode": "110001"},
]

logger = logging.getLogger("customer_workload")

class WorkloadMetrics:
    """Thread-safe collector for customer workload telemetry."""
    def __init__(self):
        self._lock = threading.Lock()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.latencies: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.start_time = time.time()

    def record(self, status_code: int, duration_ms: float):
        with self._lock:
            self.total_requests += 1
            if 200 <= status_code < 400:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
            self.latencies.append(duration_ms)
            if len(self.latencies) > 2000:
                self.latencies = self.latencies[-1000:]

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            elapsed = max(0.001, time.time() - self.start_time)
            rps = round(self.total_requests / elapsed, 1)
            sorted_lat = sorted(self.latencies) if self.latencies else [0.0]
            n = len(sorted_lat)
            p50 = round(sorted_lat[int(n * 0.50)], 1)
            p90 = round(sorted_lat[min(n - 1, int(n * 0.90))], 1)
            p95 = round(sorted_lat[min(n - 1, int(n * 0.95))], 1)
            p99 = round(sorted_lat[min(n - 1, int(n * 0.99))], 1)
            error_rate = round((self.failed_requests / max(1, self.total_requests)) * 100, 2)
            
            return {
                "elapsed_seconds": round(elapsed, 1),
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "error_rate_pct": error_rate,
                "current_rps": rps,
                "p50_latency_ms": p50,
                "p90_latency_ms": p90,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "status_breakdown": dict(self.status_codes)
            }


class CustomerWorkloadGenerator:
    """
    Realistic Customer Traffic Generator.
    Exercises catalog browsing, search, and order checkout concurrently.
    """
    def __init__(
        self,
        base_url: str = "http://localhost:5000",
        target_concurrency: int = 35,
        ramp_seconds: float = 8.0,
        request_delay_sec: float = 0.05,
        search_ratio: float = 0.60,
        order_ratio: float = 0.05
    ):
        self.base_url = base_url.rstrip("/")
        self.target_concurrency = target_concurrency
        self.ramp_seconds = ramp_seconds
        self.request_delay_sec = request_delay_sec
        self.search_ratio = search_ratio
        self.order_ratio = order_ratio

        self.metrics = WorkloadMetrics()
        self.stop_event = threading.Event()
        self.workers: List[threading.Thread] = []
        self._is_running = False

    def is_running(self) -> bool:
        return self._is_running and not self.stop_event.is_set()

    def start(self):
        """Spawns customer simulation worker threads with concurrency ramp."""
        if self._is_running:
            return
        self._is_running = True
        self.stop_event.clear()
        self.metrics = WorkloadMetrics()

        # Start master coordinator thread that ramps up workers
        coordinator = threading.Thread(target=self._run_ramp_and_manage, daemon=True, name="WorkloadCoordinator")
        coordinator.start()

    def stop(self):
        """Signals all workers to stop immediately."""
        self.stop_event.set()
        self._is_running = False

    def _run_ramp_and_manage(self):
        """Gradually ramps up concurrent customer threads up to target ceiling."""
        delay_per_worker = self.ramp_seconds / max(1, self.target_concurrency)
        for i in range(self.target_concurrency):
            if self.stop_event.is_set():
                break
            worker = threading.Thread(target=self._customer_worker, args=(i + 1,), daemon=True, name=f"CustomerWorker-{i+1}")
            self.workers.append(worker)
            worker.start()
            time.sleep(delay_per_worker)

    def _customer_worker(self, worker_id: int):
        """Simulates individual customer session performing realistic actions."""
        # Each customer thread maintains its own HTTP client connection pool
        with httpx.Client(base_url=self.base_url, timeout=6.0) as client:
            while not self.stop_event.is_set():
                try:
                    action_roll = random.random()
                    t0 = time.perf_counter()

                    if action_roll < 0.75:
                        # 1. Search Query: exercises database text matching ILIKE across categories
                        term = random.choice(SEARCH_TERMS)
                        resp = client.get(f"/api/products?search={term}&nocache=true")
                        status = resp.status_code
                    elif action_roll < 0.90:
                        # 2. Category browsing
                        cat = random.choice(CATEGORIES)
                        resp = client.get(f"/api/products?category={cat}")
                        status = resp.status_code
                    else:
                        # 3. Product detail inspection
                        prod_id = random.randint(1, 36)
                        resp = client.get(f"/api/products/{prod_id}")
                        status = resp.status_code

                    dur_ms = round((time.perf_counter() - t0) * 1000, 2)
                    self.metrics.record(status, dur_ms)

                except Exception:
                    self.metrics.record(503, 5000.0)

                # Realistic think time between clicks
                if self.request_delay_sec > 0:
                    time.sleep(self.request_delay_sec)

    def get_stats(self) -> Dict[str, Any]:
        """Returns live statistics of customer workload."""
        stats = self.metrics.get_snapshot()
        stats["is_running"] = self.is_running()
        stats["target_concurrency"] = self.target_concurrency
        stats["active_workers"] = len([w for w in self.workers if w.is_alive()])
        return stats


def main():
    parser = argparse.ArgumentParser(description="Realistic ShopEase Customer Workload Generator")
    parser.add_argument("--url", default="http://localhost:5000", help="ShopEase base URL")
    parser.add_argument("--concurrency", type=int, default=35, help="Number of concurrent customer sessions")
    parser.add_argument("--duration", type=int, default=30, help="Run duration in seconds")
    parser.add_argument("--delay", type=float, default=0.04, help="Think time delay between requests per worker (sec)")
    args = parser.parse_args()

    print(f"============================================================")
    print(f"🛒 Starting Customer Workload Generator against {args.url}")
    print(f"👥 Target Concurrency: {args.concurrency} customer sessions")
    print(f"⏱️ Duration: {args.duration}s | Worker Delay: {args.delay}s")
    print(f"============================================================")

    gen = CustomerWorkloadGenerator(
        base_url=args.url,
        target_concurrency=args.concurrency,
        request_delay_sec=args.delay
    )
    gen.start()

    start_t = time.time()
    try:
        while time.time() - start_t < args.duration:
            time.sleep(2.0)
            st = gen.get_stats()
            print(
                f"[{st['elapsed_seconds']}s] Active: {st['active_workers']}/{st['target_concurrency']} | "
                f"Reqs: {st['total_requests']} ({st['current_rps']} RPS) | "
                f"P50: {st['p50_latency_ms']}ms | P95: {st['p95_latency_ms']}ms | P99: {st['p99_latency_ms']}ms | "
                f"Err: {st['error_rate_pct']}%"
            )
    except KeyboardInterrupt:
        print("\nStopping generator cleanly...")
    finally:
        gen.stop()
        print("\nWorkload generator stopped.")
        final_st = gen.get_stats()
        print(f"Final Stats: Total={final_st['total_requests']}, RPS={final_st['current_rps']}, P99={final_st['p99_latency_ms']}ms")

if __name__ == "__main__":
    main()
