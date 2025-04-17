"""Tests for the HomeyAssistant agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.homey_assistant import HomeyAssistant


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "llm_config": {},
        "require_confirmation": True,
        "devices": [
            {
                "id": "light_1",
                "type": "light",
                "zone": "woonkamer"
            },
            {
                "id": "thermostat_1",
                "type": "thermostat",
                "zone": "woonkamer"
            }
        ]
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    return AsyncMock()


@pytest.fixture
def homey_assistant(mock_config, mock_mqtt_client):
    """Create a HomeyAssistant instance with mock dependencies."""
    return HomeyAssistant(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_process_control_intent(homey_assistant):
    """Test processing a control intent."""
    input_data = {
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["status"] == "success"
    assert "I'll turning on the light in the woonkamer" in result["response"]
    assert len(result["actions"]) == 1
    assert result["actions"][0]["device_id"] == "light_1"
    assert result["actions"][0]["capability"] == "onoff"
    assert result["actions"][0]["value"] == "on"
    assert result["requires_confirmation"] is True


@pytest.mark.asyncio
async def test_process_sensor_intent(homey_assistant):
    """Test processing a sensor reading intent."""
    input_data = {
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer",
            "confidence": 0.95
        },
        "sensor_data": {
            "type": "temperature",
            "zone": "woonkamer",
            "value": 22.5,
            "timestamp": "2024-03-20T10:00:00"
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["status"] == "success"
    assert "The temperature in the woonkamer is 22.5" in result["response"]
    assert len(result["actions"]) == 0
    assert result["requires_confirmation"] is False


@pytest.mark.asyncio
async def test_process_unknown_intent(homey_assistant):
    """Test processing an unknown intent."""
    input_data = {
        "intent": {
            "type": "unknown",
            "confidence": 0.1
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["status"] == "success"
    assert "I'm not sure what you want me to do" in result["response"]
    assert len(result["actions"]) == 0
    assert result["requires_confirmation"] is True


@pytest.mark.asyncio
async def test_process_error(homey_assistant):
    """Test error handling in process method."""
    input_data = {}  # Missing required intent
    
    result = await homey_assistant.process(input_data)
    
    assert result["status"] == "error"
    assert "No intent provided" in result["error"]


@pytest.mark.asyncio
async def test_needs_confirmation(homey_assistant):
    """Test confirmation requirement logic."""
    # Test low confidence
    intent = {"confidence": 0.5}
    assert homey_assistant._needs_confirmation(intent) is True
    
    # Test high confidence
    intent = {"confidence": 0.9}
    assert homey_assistant._needs_confirmation(intent) is True  # Because require_confirmation is True
    
    # Test destructive action
    intent = {"type": "control", "value": "off", "confidence": 0.95}
    assert homey_assistant._needs_confirmation(intent) is True
    
    # Test safe action
    intent = {"type": "control", "value": "on", "confidence": 0.95}
    assert homey_assistant._needs_confirmation(intent) is True  # Still true due to config 