from prometheus_client import Counter, Histogram


DECISION_COUNTER = Counter(
    "pcfi_decisions_total",
    "Count of PCFI decisions by outcome.",
    labelnames=["outcome"],
)

LATENCY_HISTOGRAM = Histogram(
    "pcfi_middleware_latency_ms",
    "PCFI middleware latency in milliseconds.",
    buckets=(1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000),
)

