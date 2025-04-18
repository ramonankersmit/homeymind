"""Tests for the SensorAgent class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.sensor_agent import SensorAgent
from app.core.config import LLMConfig, OpenAIConfig

@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-sensor",
        openai=OpenAIConfig(
            model="test-model",
            api_type="openai",
            api_key="test-key"
        ),
        devices={
            "temp_1": [{"id": "temp_1", "type": "temperature_sensor", "zone": "woonkamer"}],
            "hum_1": [{"id": "hum_1", "type": "humidity_sensor", "zone": "woonkamer"}],
            "motion_1": [{"id": "motion_1", "type": "motion_sensor", "zone": "woonkamer"}]
        }
    )

@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    return AsyncMock()

@pytest.fixture
def sensor_agent(mock_config, mock_mqtt_client):
    """Create a SensorAgent instance with mocked dependencies."""
    return SensorAgent(mock_config, mock_mqtt_client)

@pytest.mark.asyncio
async def test_process_temperature(sensor_agent, mock_mqtt_client):
    """Test processing temperature sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": 21.5,
        "unit": "°C",
        "timestamp": "2024-03-20T10:00:00"
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "success"
    assert "temperature" in result
    assert result["temperature"]["value"] == 21.5
    assert result["temperature"]["zone"] == "woonkamer"
    assert result["temperature"]["unit"] == "°C"
    assert "timestamp" in result["temperature"]
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_humidity(sensor_agent, mock_mqtt_client):
    """Test processing humidity sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": 45.0,
        "unit": "%",
        "timestamp": "2024-03-20T10:00:00"
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "humidity",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "success"
    assert "humidity" in result
    assert result["humidity"]["value"] == 45.0
    assert result["humidity"]["zone"] == "woonkamer"
    assert result["humidity"]["unit"] == "%"
    assert "timestamp" in result["humidity"]
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_motion(sensor_agent, mock_mqtt_client):
    """Test processing motion sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": True,
        "timestamp": "2024-03-20T10:00:00"
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "motion",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "success"
    assert "motion" in result
    assert result["motion"]["value"] is True
    assert result["motion"]["zone"] == "woonkamer"
    assert "timestamp" in result["motion"]
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_multiple_sensors(sensor_agent, mock_mqtt_client):
    """Test processing multiple sensor types."""
    # Setup mock device status for different calls
    mock_mqtt_client.get_status.side_effect = [
        {"value": 21.5, "unit": "°C", "timestamp": "2024-03-20T10:00:00"},
        {"value": 45.0, "unit": "%", "timestamp": "2024-03-20T10:00:00"},
        {"value": True, "timestamp": "2024-03-20T10:00:00"}
    ]
    
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "all",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "success"
    assert "temperature" in result
    assert "humidity" in result
    assert "motion" in result
    
    assert mock_mqtt_client.get_status.call_count == 3

@pytest.mark.asyncio
async def test_process_error(sensor_agent, mock_mqtt_client):
    """Test error handling in sensor processing."""
    # Setup mock to raise exception
    mock_mqtt_client.get_status.side_effect = Exception("Test error")
    
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "error"
    assert "Test error" in result["message"]

@pytest.mark.asyncio
async def test_process_invalid_device(sensor_agent):
    """Test processing with invalid device type."""
    result = await sensor_agent.process({
        "intent": {
            "type": "sensor_read",
            "device_type": "invalid",
            "zone": "woonkamer"
        }
    })
    
    assert result["status"] == "error"
    assert "Invalid device type" in result["message"]

@pytest.mark.asyncio
async def test_process_sensor_data(mock_config, mock_mqtt_client):
    """Test processing sensor data."""
    agent = SensorAgent(mock_config, mock_mqtt_client)
    
    # Test temperature sensor
    response = await agent.process_sensor_data("temp_1", 22.5)
    assert "temperatuur" in response.lower()
    assert "22.5" in response
    assert "woonkamer" in response.lower()
    
    # Test humidity sensor
    response = await agent.process_sensor_data("hum_1", 45.0)
    assert "luchtvochtigheid" in response.lower()
    assert "45.0" in response
    assert "woonkamer" in response.lower()
    
    # Test motion sensor
    response = await agent.process_sensor_data("motion_1", 1)
    assert "beweging" in response.lower()
    assert "woonkamer" in response.lower()
    
    # Test unknown sensor
    response = await agent.process_sensor_data("unknown", 42)
    assert "unknown" in response.lower()
    assert "42" in response 