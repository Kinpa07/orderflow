from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently being processed",
    ["method", "endpoint"],
)

cache_results_total = Counter(
    "cache_results_total",
    "Tenant config cache hits and misses",
    ["result"],
)

order_processing_duration_seconds = Histogram(
    "order_processing_duration_seconds",
    "Order processing duration from PENDING to SHIPPED",
)

webhook_deliveries_total = Counter(
    "webhook_deliveries_total",
    "Webhook delivery outcomes",
    ["status"],
)

webhook_delivery_duration_seconds = Histogram(
    "webhook_delivery_duration_seconds",
    "Webhook delivery latency in seconds",
)

dead_letter_queue_depth = Gauge(
    "dead_letter_queue_depth",
    "Number of unresolved dead-letter webhook entries",
)
