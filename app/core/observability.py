import structlog
from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any
import time

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.BoundLogger,
    cache_logger_on_first_use=True,
)

# Metrics
TOOL_CALLS = Counter(
    'tool_calls_total',
    'Total number of tool calls',
    ['tool_name', 'status']
)

TOOL_LATENCY = Histogram(
    'tool_latency_seconds',
    'Tool execution latency in seconds',
    ['tool_name']
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions',
    'Number of active sessions'
)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with the given name."""
    return structlog.get_logger(name)

class ToolMetrics:
    """Metrics wrapper for tool execution."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            TOOL_LATENCY.labels(tool_name=self.tool_name).observe(duration)
            status = "success" if exc_type is None else "error"
            TOOL_CALLS.labels(tool_name=self.tool_name, status=status).inc()

class SessionMetrics:
    """Metrics wrapper for sessions."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
    
    def __enter__(self):
        ACTIVE_SESSIONS.inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        ACTIVE_SESSIONS.dec()

def log_tool_call(logger: structlog.BoundLogger, tool_name: str, input_data: Dict[str, Any]) -> None:
    """Log a tool call."""
    logger.info(
        "tool_call.start",
        tool_name=tool_name,
        input_data=input_data
    )

def log_tool_result(logger: structlog.BoundLogger, tool_name: str, result: Dict[str, Any]) -> None:
    """Log a tool result."""
    logger.info(
        "tool_call.end",
        tool_name=tool_name,
        result=result
    )

def log_error(logger: structlog.BoundLogger, error: Exception, context: Dict[str, Any] = None) -> None:
    """Log an error with context."""
    logger.error(
        "error",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {}
    ) 