"""Tests for the SensorAgent class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.sensor_agent import SensorAgent

@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "config_list": [{"model": "test-model"}],
        "temperature": 0.7
    }

@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    client = Mock()
    client.get_status = Mock(return_value={"value": 21.5})
    return client

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
        "unit": "°C"
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    })
    
    assert "temperature" in result
    assert result["temperature"]["value"] == 21.5
    assert result["temperature"]["zone"] == "woonkamer"
    assert result["temperature"]["unit"] == "°C"
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_humidity(sensor_agent, mock_mqtt_client):
    """Test processing humidity sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": 45.0,
        "unit": "%"
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "humidity",
            "zone": "woonkamer"
        }
    })
    
    assert "humidity" in result
    assert result["humidity"]["value"] == 45.0
    assert result["humidity"]["zone"] == "woonkamer"
    assert result["humidity"]["unit"] == "%"
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_motion(sensor_agent, mock_mqtt_client):
    """Test processing motion sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": True
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "motion",
            "zone": "woonkamer"
        }
    })
    
    assert "motion" in result
    assert result["motion"]["value"] is True
    assert result["motion"]["zone"] == "woonkamer"
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_contact(sensor_agent, mock_mqtt_client):
    """Test processing contact sensor data."""
    # Setup mock device status
    mock_mqtt_client.get_status.return_value = {
        "value": False
    }
    
    result = await sensor_agent.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "contact",
            "zone": "voordeur"
        }
    })
    
    assert "contact" in result
    assert result["contact"]["value"] is False
    assert result["contact"]["zone"] == "voordeur"
    
    mock_mqtt_client.get_status.assert_called_once()

@pytest.mark.asyncio
async def test_process_multiple_sensors(sensor_agent, mock_mqtt_client):
    """Test processing multiple sensor types."""
    # Setup mock device status for different calls
    mock_mqtt_client.get_status.side_effect = [
        {"value": 21.5, "unit": "°C"},
        {"value": 45.0, "unit": "%"},
        {"value": True}
    ]
    
    result = await sensor_agent.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "all",
            "zone": "woonkamer"
        }
    })
    
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
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    })
    
    assert "error" in result
    assert result["error"] == "Test error" 