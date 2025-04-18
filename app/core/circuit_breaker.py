from tenacity import retry, stop_after_delay, wait_exponential, retry_if_exception_type
from typing import Type, Any, Callable, Optional
import asyncio
import time
from app.core.observability import get_logger, log_error
from app.core.metrics import update_circuit_breaker_metrics

class CircuitBreaker:
    """Circuit breaker for MQTT operations."""
    
    def __init__(
        self,
        name: str,
        max_delay: float = 2.0,
        max_retries: int = 3,
        exceptions: tuple[Type[Exception], ...] = (Exception,),
        open_timeout: float = 30.0,
        success_threshold: int = 3
    ):
        self.name = name
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.exceptions = exceptions
        self.open_timeout = open_timeout
        self.success_threshold = success_threshold
        self.logger = get_logger(f"circuit_breaker.{name}")
        self._state = "closed"
        self._last_failure_time = 0
        self._success_count = 0
        self._last_state_change = time.time()
        
        # Initialize metrics
        update_circuit_breaker_metrics(
            breaker_name=self.name,
            state=self._state
        )
    
    @property
    def state(self) -> str:
        return self._state
    
    def _set_state(self, new_state: str) -> None:
        old_state = self._state
        self._state = new_state
        
        # Update metrics
        update_circuit_breaker_metrics(
            breaker_name=self.name,
            state=new_state
        )
        
        # Log state change
        self.logger.info(
            "circuit_breaker.state_change",
            breaker_name=self.name,
            old_state=old_state,
            new_state=new_state
        )
    
    def _should_try_half_open(self) -> bool:
        if self._state == "open":
            return time.time() - self._last_failure_time >= self.open_timeout
        return False
    
    def _update_success_count(self) -> None:
        self._success_count += 1
        if self._success_count >= self.success_threshold:
            recovery_time = time.time() - self._last_state_change
            update_circuit_breaker_metrics(
                breaker_name=self.name,
                state="closed",
                recovery_time=recovery_time
            )
            self._set_state("closed")
            self._success_count = 0
    
    async def execute(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with circuit breaker protection."""
        if self._state == "open":
            if self._should_try_half_open():
                self._set_state("half-open")
            else:
                update_circuit_breaker_metrics(
                    breaker_name=self.name,
                    state="open",
                    operation_type="execute",
                    status="rejected"
                )
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")
        
        try:
            @retry(
                stop=stop_after_delay(self.max_delay),
                wait=wait_exponential(multiplier=0.1, max=1.0),
                retry=retry_if_exception_type(self.exceptions),
                reraise=True
            )
            async def _execute():
                return await func(*args, **kwargs)
            
            result = await _execute()
            
            if self._state == "half-open":
                self._update_success_count()
            else:
                self._set_state("closed")
            
            update_circuit_breaker_metrics(
                breaker_name=self.name,
                state=self._state,
                operation_type="execute",
                status="success"
            )
            
            return result
            
        except Exception as e:
            self._last_failure_time = time.time()
            self._success_count = 0
            
            update_circuit_breaker_metrics(
                breaker_name=self.name,
                state=self._state,
                error=e,
                operation_type="execute",
                status="error"
            )
            
            log_error(
                self.logger,
                e,
                {
                    "breaker_name": self.name,
                    "state": self._state,
                    "args": args,
                    "kwargs": kwargs
                }
            )
            
            if self._state == "half-open":
                self._set_state("open")
            else:
                self._set_state("open")
            
            raise CircuitBreakerError(f"Circuit breaker {self.name} failed: {str(e)}")

class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass

class CircuitBreakerOpen(CircuitBreakerError):
    """Exception raised when circuit breaker is open."""
    pass 