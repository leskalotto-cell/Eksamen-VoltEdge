from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "voltedge_request_count",
    "Total number of HTTP requests processed",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "voltedge_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

SESSION_EVENTS_TOTAL = Counter(
    "voltedge_session_events_total",
    "Total number of charging session lifecycle events",
    ["event"],
)
