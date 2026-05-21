#!/usr/bin/env python3
"""
Load generator for OrderFlow — populates the Grafana dashboard with real data.

Creates tenants, submits orders (valid, price-too-high, and bad-auth), and
runs a local webhook receiver so the webhook health panel also lights up.

Run from the repo root with the full Docker Compose stack up:
    python load_test.py

Note: port 9999 must be free on your machine (the webhook receiver binds to it).
"""

import asyncio
import random
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

from config import WEBHOOK_RETRY_COUNT

BASE_URL = "http://localhost:8000"
WEBHOOK_PORT = 9999
# host.docker.internal resolves to the host machine from inside Docker Desktop
WEBHOOK_URL = f"http://host.docker.internal:{WEBHOOK_PORT}/webhook"
WEBHOOK_FAIL_URL = f"http://host.docker.internal:{WEBHOOK_PORT}/webhook/fail"

_webhook_count = 0
_webhook_fail_count = 0
_webhook_lock = threading.Lock()


class _WebhookReceiver(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        global _webhook_count, _webhook_fail_count
        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        # /webhook/fail always 500s so the order-processor exhausts retries
        # and the order lands in the dead-letter queue.
        if self.path.startswith("/webhook/fail"):
            self.send_response(500)
            self.end_headers()
            with _webhook_lock:
                _webhook_fail_count += 1
            return
        self.send_response(200)
        self.end_headers()
        with _webhook_lock:
            _webhook_count += 1

    def log_message(self, *_: object) -> None:
        pass  # silence the default access log


def _start_webhook_server() -> None:
    HTTPServer(("0.0.0.0", WEBHOOK_PORT), _WebhookReceiver).serve_forever()


def _bucket(r: httpx.Response | BaseException) -> str:
    if isinstance(r, BaseException):
        return "err"
    return f"{r.status_code // 100}xx"


async def main() -> None:
    threading.Thread(target=_start_webhook_server, daemon=True).start()
    print(f"Webhook receiver listening on :{WEBHOOK_PORT}\n")

    totals: Counter[str] = Counter()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as c:

        # ------------------------------------------------------------------
        # Create tenants
        # 3 normal tenants (max_price=1000) + 1 restricted (max_price=50).
        # Fewer tenants means fewer total orders, so the order-processor can
        # finish within the wait window and webhooks actually get delivered.
        # ------------------------------------------------------------------
        print("Creating tenants...")
        tenants: list[tuple[int, str]] = []
        for i in range(1, 4):
            r = await c.post(
                "/tenants/",
                json={
                    "company_name": f"Load Tenant {i}",
                    "contact_name": "Load Test",
                    "email": f"load{i}@example.com",
                    "phone": "+1-555-0100",
                    "config": {"maximum_price": 1000.0},
                    "webhook_url": WEBHOOK_URL,
                },
            )
            r.raise_for_status()
            d = r.json()
            tenants.append((d["id"], d["api_key"]))
            print(f"  Tenant {i}: id={d['id']}")

        r = await c.post(
            "/tenants/",
            json={
                "company_name": "Restricted Tenant",
                "contact_name": "Load Test",
                "email": "restricted@example.com",
                "phone": "+1-555-0199",
                "config": {"maximum_price": 50.0},
                "webhook_url": WEBHOOK_URL,
            },
        )
        r.raise_for_status()
        rd = r.json()
        restricted_id, restricted_key = rd["id"], rd["api_key"]
        print(f"  Restricted: id={restricted_id} (max_price=50.0)")

        # Tenant whose webhook URL always 500s — orders succeed but their
        # webhook delivery exhausts retries -> dead letter queue increments.
        r = await c.post(
            "/tenants/",
            json={
                "company_name": "Failing Webhook Tenant",
                "contact_name": "Load Test",
                "email": "fail@example.com",
                "phone": "+1-555-0666",
                "config": {"maximum_price": 1000.0},
                "webhook_url": WEBHOOK_FAIL_URL,
            },
        )
        r.raise_for_status()
        fd = r.json()
        fail_tid, fail_key = fd["id"], fd["api_key"]
        print(f"  FailingWebhook: id={fail_tid} (webhook 500s -> DLQ)\n")

        # ------------------------------------------------------------------
        # Valid orders — two waves per tenant with a sleep between them.
        #
        # Wave 1 (1 request, sequential): populates the auth cache for this
        # API key so the wave-2 concurrent requests get cache hits instead of
        # all racing to miss simultaneously.
        #
        # Sleep between waves: gives Prometheus time for a second scrape so
        # rate() has at least 2 samples → HTTP latency panel gets real data.
        # ------------------------------------------------------------------
        print("Submitting valid orders (2 waves per tenant, 3 tenants)...")
        order_ids_by_tenant: dict[int, list[int]] = {}
        for i, (tid, key) in enumerate(tenants, 1):
            # Wave 1 — single warm-up request (cache miss, populates cache)
            warm = await c.post(
                f"/tenants/{tid}/orders/",
                json={"price": round(random.uniform(10.0, 499.0), 2)},
                headers={"api-key": key},
            )
            totals[_bucket(warm)] += 1
            ids: list[int] = []
            if warm.status_code == 200:
                ids.append(warm.json()["id"])

            # Wave 2 — 7 concurrent requests (cache hits from here on)
            tasks = [
                c.post(
                    f"/tenants/{tid}/orders/",
                    json={"price": round(random.uniform(10.0, 499.0), 2)},
                    headers={"api-key": key},
                )
                for _ in range(7)
            ]
            batch = await asyncio.gather(*tasks, return_exceptions=True)
            for resp in batch:
                totals[_bucket(resp)] += 1
                if not isinstance(resp, BaseException) and resp.status_code == 200:
                    ids.append(resp.json()["id"])

            order_ids_by_tenant[tid] = ids
            ok = sum(
                1
                for resp in [warm, *batch]
                if not isinstance(resp, BaseException) and resp.status_code == 200
            )
            print(f"  Tenant {i} ({tid}): {ok} orders accepted")

        print(f"  running totals: {dict(totals)}")

        # Sleep so Prometheus gets a second scrape before the next burst.
        # This is what makes the HTTP latency histogram visible in the panel.
        print("  (sleeping 20s so Prometheus can scrape mid-load...)")
        await asyncio.sleep(20)

        # ------------------------------------------------------------------
        # Orders for the failing-webhook tenant. Order creation succeeds;
        # webhook delivery exhausts WEBHOOK_RETRY_COUNT retries with backoff
        # (1s + 2s + 4s + 3*timeout) and the order lands in the DLQ.
        # ------------------------------------------------------------------
        print("Submitting orders to failing-webhook tenant (expect DLQ growth)...")
        bad_webhook_tasks = [
            c.post(
                f"/tenants/{fail_tid}/orders/",
                json={"price": round(random.uniform(10.0, 499.0), 2)},
                headers={"api-key": fail_key},
            )
            for _ in range(3)
        ]
        responses = await asyncio.gather(*bad_webhook_tasks, return_exceptions=True)
        for resp in responses:
            totals[_bucket(resp)] += 1
        print(f"  3 orders submitted, totals: {dict(totals)}\n")

        # ------------------------------------------------------------------
        # GET individual orders — 4 per tenant, concurrent.
        # Auth key is already cached so these all hit the cache.
        # ------------------------------------------------------------------
        print("\nFetching individual orders (cache hits)...")
        for tid, key in tenants:
            ids = order_ids_by_tenant.get(tid, [])
            if not ids:
                continue
            tasks = [
                c.get(
                    f"/tenants/{tid}/orders/{random.choice(ids)}",
                    headers={"api-key": key},
                )
                for _ in range(4)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for resp in responses:
                totals[_bucket(resp)] += 1
        print(f"  running totals: {dict(totals)}\n")

        # ------------------------------------------------------------------
        # 4xx traffic — spread across ~3 scrape intervals (45s+) so that the
        # error-rate counter increases between scrapes. A single tight burst
        # completes within one scrape interval and rate() returns 0 forever
        # (counter goes 0 -> 25 in <1s, all subsequent scrapes see the same
        # static value).
        # ------------------------------------------------------------------
        print("Submitting 4xx traffic spread over ~50s (400s + 401s in 5 waves)...")
        first_tid = tenants[0][0]
        for wave in range(5):
            bad_price = [
                c.post(
                    f"/tenants/{restricted_id}/orders/",
                    json={"price": round(random.uniform(100.0, 500.0), 2)},
                    headers={"api-key": restricted_key},
                )
                for _ in range(2)
            ]
            bad_auth = [
                c.get(
                    f"/tenants/{first_tid}/orders/",
                    headers={"api-key": "invalid-key-xyz"},
                )
                for _ in range(3)
            ]
            responses = await asyncio.gather(
                *bad_price, *bad_auth, return_exceptions=True
            )
            for resp in responses:
                totals[_bucket(resp)] += 1
            print(f"  wave {wave + 1}/5: totals {dict(totals)}")
            if wave < 4:
                await asyncio.sleep(12)  # >= 1 scrape interval (15s) over the 5 waves
        print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("--- Request summary ---")
    for bucket, count in sorted(totals.items()):
        print(f"  {bucket}: {count}")
    valid_orders = totals.get("2xx", 0) - len(tenants)  # subtract tenant creates
    print(f"  Total: {sum(totals.values())}")

    # 3 tenants * 8 orders * ~2.4s each ~= 58s processing time.
    # Wait 120s so the order-processor can drain fully before we exit
    # (if we exit early, the daemon webhook receiver dies and remaining
    # deliveries fail → dead letter accumulates).
    wait = 120
    print(f"\nWaiting {wait}s for order-processor to drain + webhooks to arrive...")
    print("(the order-processor takes ~2.4s per order; ~24 orders * 2.4s ~= 58s)")
    for remaining in range(wait, 0, -10):
        await asyncio.sleep(10)
        with _webhook_lock:
            wh = _webhook_count
        print(f"  {remaining}s remaining | webhooks received so far: {wh}")

    with _webhook_lock:
        final = _webhook_count
        final_fail = _webhook_fail_count

    print(f"\nWebhook deliveries received: {final} / ~{valid_orders} expected")
    print(
        "Failing webhook hits "
        f"(expected 3 orders * 2 transitions * {WEBHOOK_RETRY_COUNT} retries = 18): "
        f"{final_fail}"
    )
    print(
        "\nGrafana: http://localhost:3000"
        "\n  -> find 'OrderFlow' dashboard"
        "\n  -> set time range to 'Last 15 minutes'"
    )


if __name__ == "__main__":
    asyncio.run(main())
