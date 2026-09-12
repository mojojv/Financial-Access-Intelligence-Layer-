"""Prometheus metrics definitions for Financial Access Intelligence Layer.

Exposes key operational metrics for monitoring FAI score calculations,
Open Payments executions, barrier detections and API request volumes.
"""
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, CollectorRegistry, REGISTRY

    # --- FAI Scoring Metrics ---

    FAI_SCORE_CALCULATED = Counter(
        "fai_score_calculated_total",
        "Total number of FAI scores calculated",
        ["methodology", "severity"],
    )

    FAI_SCORE_VALUE = Histogram(
        "fai_overall_score",
        "Distribution of overall FAI scores (0-100)",
        buckets=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    )

    FAI_CALCULATION_DURATION = Histogram(
        "fai_calculation_duration_seconds",
        "Time spent on FAI score calculation pipeline",
        buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    )

    # --- Barrier Detection Metrics ---

    BARRIERS_DETECTED = Counter(
        "barriers_detected_total",
        "Total barriers detected by dimension and severity",
        ["dimension", "severity", "barrier_code"],
    )

    ACTIVE_BARRIERS = Gauge(
        "active_barriers_current",
        "Number of currently active (non-resolved) barriers",
    )

    # --- Intervention Metrics ---

    INTERVENTIONS_RECOMMENDED = Counter(
        "interventions_recommended_total",
        "Total interventions recommended",
        ["intervention_type"],
    )

    INTERVENTIONS_EXECUTED = Counter(
        "interventions_executed_total",
        "Total interventions executed via Open Payments",
        ["status", "asset_code"],
    )

    # --- Open Payments / ILP Metrics ---

    OPEN_PAYMENTS_REQUESTS = Counter(
        "open_payments_api_requests_total",
        "Total Open Payments API requests made",
        ["operation", "status"],
    )

    PAYMENT_EXECUTION_DURATION = Histogram(
        "payment_execution_duration_seconds",
        "Duration of Open Payments execution flow",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    )

    PAYMENT_AMOUNT_USD = Summary(
        "payment_amount_usd",
        "Distribution of payment amounts executed in USD",
    )

    # --- HTTP API Metrics ---

    HTTP_REQUESTS = Counter(
        "http_requests_total",
        "Total HTTP requests to FAIL API",
        ["method", "endpoint", "status_code"],
    )

    HTTP_REQUEST_DURATION = Histogram(
        "http_request_duration_seconds",
        "HTTP request processing duration",
        ["method", "endpoint"],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    )

    _METRICS_AVAILABLE = True

except ImportError:
    # prometheus_client not installed — create no-op stubs
    class _NoOpMetric:
        def labels(self, **kwargs): return self
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass

    FAI_SCORE_CALCULATED = _NoOpMetric()  # type: ignore
    FAI_SCORE_VALUE = _NoOpMetric()  # type: ignore
    FAI_CALCULATION_DURATION = _NoOpMetric()  # type: ignore
    BARRIERS_DETECTED = _NoOpMetric()  # type: ignore
    ACTIVE_BARRIERS = _NoOpMetric()  # type: ignore
    INTERVENTIONS_RECOMMENDED = _NoOpMetric()  # type: ignore
    INTERVENTIONS_EXECUTED = _NoOpMetric()  # type: ignore
    OPEN_PAYMENTS_REQUESTS = _NoOpMetric()  # type: ignore
    PAYMENT_EXECUTION_DURATION = _NoOpMetric()  # type: ignore
    PAYMENT_AMOUNT_USD = _NoOpMetric()  # type: ignore
    HTTP_REQUESTS = _NoOpMetric()  # type: ignore
    HTTP_REQUEST_DURATION = _NoOpMetric()  # type: ignore

    _METRICS_AVAILABLE = False
