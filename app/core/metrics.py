from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Counter, Gauge, Histogram
from starlette.responses import Response
from typing import Dict, Any

router = APIRouter()

# Circuit Breaker Metrics
CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Current state of the circuit breaker",
    ["breaker_name"]
)

CIRCUIT_BREAKER_ERRORS = Counter(
    "circuit_breaker_errors_total",
    "Total number of circuit breaker errors",
    ["breaker_name", "error_type"]
)

CIRCUIT_BREAKER_RECOVERY_TIME = Histogram(
    "circuit_breaker_recovery_time_seconds",
    "Time taken for circuit breaker to recover",
    ["breaker_name"]
)

CIRCUIT_BREAKER_OPERATIONS = Counter(
    "circuit_breaker_operations_total",
    "Total number of circuit breaker operations",
    ["breaker_name", "operation_type", "status"]
)

def update_circuit_breaker_metrics(
    breaker_name: str,
    state: str,
    error: Exception = None,
    recovery_time: float = None,
    operation_type: str = None,
    status: str = None
) -> None:
    """Update circuit breaker metrics."""
    CIRCUIT_BREAKER_STATE.labels(breaker_name=breaker_name).set(
        0 if state == "closed" else 1 if state == "open" else 2
    )
    
    if error:
        CIRCUIT_BREAKER_ERRORS.labels(
            breaker_name=breaker_name,
            error_type=error.__class__.__name__
        ).inc()
    
    if recovery_time:
        CIRCUIT_BREAKER_RECOVERY_TIME.labels(
            breaker_name=breaker_name
        ).observe(recovery_time)
    
    if operation_type and status:
        CIRCUIT_BREAKER_OPERATIONS.labels(
            breaker_name=breaker_name,
            operation_type=operation_type,
            status=status
        ).inc()

@router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    ) 