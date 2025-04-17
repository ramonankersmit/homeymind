"""Tests for the SensorAgent class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.sensor_agent import SensorAgent

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "name": "sensor-agent",
        "system_message": "You are a sensor data processing agent.",
        "config_list": [{"model": "test-model"}],
        "temperature": 0.7,
        "devices": [
            {
                "id": "temp_sensor_1",
                "type": "temperature",
                "zone": "woonkamer"
            },
            {
                "id": "humidity_sensor_1",
                "type": "humidity",
                "zone": "woonkamer"
            },
            {
                "id": "motion_sensor_1",
                "type": "motion",
                "zone": "woonkamer"
            }
        ]
    }

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