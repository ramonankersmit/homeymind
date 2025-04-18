import pytest
import asyncio
from unittest.mock import Mock, patch
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitBreakerOpen

@pytest.mark.asyncio
async def test_circuit_breaker_closed_state():
    breaker = CircuitBreaker("test")
    mock_func = Mock(return_value="success")
    
    result = await breaker.execute(mock_func)
    
    assert result == "success"
    assert breaker.state == "closed"
    mock_func.assert_called_once()

@pytest.mark.asyncio
async def test_circuit_breaker_retries():
    breaker = CircuitBreaker("test", max_retries=2)
    mock_func = Mock(side_effect=[Exception(), Exception(), "success"])
    
    result = await breaker.execute(mock_func)
    
    assert result == "success"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_max_retries():
    breaker = CircuitBreaker("test", max_retries=2)
    mock_func = Mock(side_effect=Exception())
    
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(mock_func)
    
    assert breaker.state == "open"
    assert mock_func.call_count == 3

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_state():
    breaker = CircuitBreaker("test", open_timeout=0.1)
    mock_func = Mock(side_effect=Exception())
    
    # Force open state
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(mock_func)
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # First call in half-open should succeed
    mock_func.side_effect = None
    mock_func.return_value = "success"
    result = await breaker.execute(mock_func)
    
    assert result == "success"
    assert breaker.state == "closed"

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure():
    breaker = CircuitBreaker("test", open_timeout=0.1)
    mock_func = Mock(side_effect=Exception())
    
    # Force open state
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(mock_func)
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # First call in half-open should fail
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(mock_func)
    
    assert breaker.state == "open"

@pytest.mark.asyncio
async def test_circuit_breaker_success_threshold():
    breaker = CircuitBreaker("test", success_threshold=2, open_timeout=0.1)
    mock_func = Mock(side_effect=Exception())
    
    # Force open state
    with pytest.raises(CircuitBreakerError):
        await breaker.execute(mock_func)
    
    # Wait for timeout
    await asyncio.sleep(0.2)
    
    # First success in half-open
    mock_func.side_effect = None
    mock_func.return_value = "success"
    result = await breaker.execute(mock_func)
    assert breaker.state == "half-open"
    
    # Second success should close circuit
    result = await breaker.execute(mock_func)
    assert breaker.state == "closed" 