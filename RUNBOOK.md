# OrderFlow Runbook

Open the Grafana dashboard at http://localhost:3000 (admin / admin). This document describes what healthy looks like for each panel and how to diagnose specific failure modes using only the dashboard and structured logs.

---

## HTTP Overview (top row)

### Request Rate
**Healthy:** Stable throughput matching your expected load. Each series is one `method + endpoint` combination.

| Signal | Problem |
|--------|---------|
| All series drop to zero | API is down or unreachable — check `docker compose ps` and `api` container logs |
| Sudden spike then plateau | Retry storm — a client is hammering a failing endpoint |
| Rate drops for one endpoint only | That route may have crashed; check for 5xx spikes at the same time |

### Error Rate
**Healthy:** 5xx rate is 0%. 4xx rate is low and stable (expected validation rejections).

| Signal | Problem |
|--------|---------|
| 5xx rate > 1% | Server-side error; check `api` container logs for Python tracebacks |
| 5xx spikes then recovers | Transient failure — Redis or Postgres briefly unavailable |
| 5xx sustained at any level | Something is consistently broken — check DB connections and Redis health |
| 4xx spike | Bad client input or auth failure; not a system health problem unless it's abnormally high |

### HTTP Latency (p50 / p95)
**Healthy:** p95 under 200 ms at typical load. The p50–p95 gap should be narrow.

| Signal | Problem |
|--------|---------|
| p95 climbing, request rate stable | Something downstream is slowing — check order processing duration and cache hit rate first |
| p95 high for all endpoints equally | Global resource pressure (DB connection pool exhaustion, Redis latency) |
| p50–p95 gap widens | Long-tail requests — usually lock contention or a slow query on specific data |

---

## Order Pipeline (second row)

### Order Processing Throughput
**Healthy:** Throughput roughly proportional to order submission rate. A lag of a few seconds is normal (Redis Stream consumer delay).

| Signal | Problem |
|--------|---------|
| Throughput drops to zero | `order-processor` is down or has stopped consuming from the Redis Stream — check `order-processor` container logs |
| Throughput low while HTTP rate is high | Orders are queuing in the stream faster than they are consumed; processor may be stalling on a slow step |
| Throughput drops, then recovers | Transient processor crash with restart — check for repeated drops |

### Order Processing Duration (p50 / p95)
**Healthy:** p95 under 5 seconds (simulated pipeline steps add expected delay).

| Signal | Problem |
|--------|---------|
| p95 climbing steadily | A processing step is slowing — cross-reference with webhook latency (slow delivery can block the processor) |
| p95 spikes at a regular interval | Retry backoff or timeout threshold being hit; check webhook delivery rate at the same timestamp |
| p95 very high, throughput low | Processor is spending most of its time waiting; likely blocked on webhook delivery to a slow endpoint |

---

## Cache (third row)

### Cache Hit Rate
**Healthy:** Above 80% under steady-state load. Expect a low hit rate on cold start while the cache warms.

| Signal | Problem |
|--------|---------|
| Hit rate drops to 0% | Redis is down or unrestarted after a crash; cache miss path falls back to DB |
| Hit rate drops after a deploy | TTL too short, or cache keys were intentionally invalidated (expected on config changes) |
| Sustained low hit rate under normal load | TTL is set too aggressively; or tenant configs are being updated very frequently |

### Cache Hits vs Misses
**Use this panel to:** Confirm cache warm-up after a Redis restart. You should see a burst of misses, then hits dominate as the cache fills. If the miss rate stays high after several minutes of traffic, the cache is not retaining entries.

---

## Webhook Health (bottom row)

### Webhook Delivery Rate
**Healthy:** Success rate matches order completion rate. Dead-letter rate is zero.

| Signal | Problem |
|--------|---------|
| Success drops, dead-letter rises | Webhook endpoint is failing; check which tenant is affected and whether their URL is reachable |
| Both rates drop to zero | Order-processor is not completing orders — check the pipeline panels first |
| Dead-letter rate non-zero but low | Isolated endpoint failure; retry budget is exhausted for some orders |

### Webhook Delivery Latency (p50 / p95)
**Healthy:** p95 under 2 seconds. Delivery is async relative to the API but runs inside the order-processor.

| Signal | Problem |
|--------|---------|
| p95 > 5 seconds | Webhook endpoint is slow; this will back up order-processor throughput if delivery is not properly async |
| p95 spikes then recovers | Intermittent network issue; retry logic should cover this — verify dead-letter depth did not grow |
| p95 grows while success rate holds | Endpoint is degraded but not failing; watch closely — it may tip into failures |

### Dead Letter Queue Depth
**Healthy:** Zero at all times.

| Color | Meaning | Action |
|-------|---------|--------|
| Green (0) | No failed deliveries | No action needed |
| Yellow (1–4) | Some deliveries exhausted retries | Check logs for affected tenants; inspect `GET /tenants/{id}/webhooks/dead-letter` |
| Red (5+) | Systematic failure | Tenant webhook endpoint is likely down; investigate and manually retry or clear after fixing |

Note: the dead-letter depth does **not** auto-resolve when the endpoint recovers. Failed entries require manual inspection and replay.

---

## Diagnosing Common Scenarios

### "Something feels slow"
1. Check p95 latency — is it the HTTP layer or the order processing duration?
2. If HTTP latency is elevated: is it all endpoints or one? The request rate panel breaks down by endpoint.
3. If order processing duration is elevated: check cache hit rate (low = extra DB reads) and webhook latency (high = processor backing up).
4. Correlate with logs using the `correlation_id` field — every log line from API receipt through the stream to the processor to webhook delivery shares the same ID.

### "Orders aren't completing"
1. Check order processing throughput — is it zero or just low?
2. Zero throughput → `order-processor` is down or not consuming from the stream; check `docker compose logs order-processor`.
3. Low throughput → processor is running but slow; check processing duration and webhook latency panels.
4. If pipeline looks fine but HTTP success rate is low → orders may be failing at submission; check 4xx/5xx rates on the creation endpoint.

### "Webhook failures accumulating"
1. Dead-letter queue depth is non-zero.
2. Check the webhook delivery rate panel — when did failures start? Match to a deployment, config change, or external outage.
3. Check delivery latency at the same time — did latency spike before failures appeared? (Slow endpoint → retries exhausted → dead-letter.)
4. Use `GET /tenants/{id}/webhooks/dead-letter` to identify affected tenants.
5. After fixing the endpoint, manually replay the failed deliveries — the depth will not clear on its own.

### "Redis went down briefly"
1. Cache hit rate drops to 0% during the outage window.
2. Order processing throughput may drop (stream consumption interrupted).
3. After Redis recovers: cache miss rate will spike then normalize as cache warms — this is expected.
4. Check for any dead-letter accumulation during the outage window — webhook deliveries that were in-flight may have failed.
