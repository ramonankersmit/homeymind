"""Tests for the HomeyAssistant."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.homey_assistant import HomeyAssistant
from app.core.config import LLMConfig, OpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-assistant",
        openai=OpenAIConfig(
            model="test-model",
            api_type="openai",
            api_key="test-key"
        ),
        devices={
            "woonkamer": [
                {"id": "light_1", "type": "light", "zone": "woonkamer"},
                {"id": "light_2", "type": "light", "zone": "woonkamer"},
                {"id": "thermostat_1", "type": "thermostat", "zone": "woonkamer"},
                {"id": "temp_1", "type": "temperature_sensor", "zone": "woonkamer"}
            ]
        }
    )


@pytest.fixture
def mock_mqtt_client():
    """Create mock MQTT client."""
    client = AsyncMock()
    client.get_device_status.return_value = {"value": 21.5}
    return client


@pytest.fixture
def homey_assistant(mock_config, mock_mqtt_client):
    """Create HomeyAssistant instance."""
    return HomeyAssistant(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_light_control_single_zone(homey_assistant):
    """Test light control for a single zone."""
    input_data = {
        "intent": {
            "type": "light_control",
            "zone": "woonkamer",
            "value": "on"
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "Turning on lights in woonkamer"
    assert len(result["actions"]) == 2
    assert result["actions"][0]["device"] == "light1"
    assert result["actions"][1]["device"] == "light2"
    assert result["actions"][0]["action"] == "set"
    assert result["actions"][0]["value"] == "on"
    assert result["actions"][1]["action"] == "set"
    assert result["actions"][1]["value"] == "on"
    assert result["needs_confirmation"] is True


@pytest.mark.asyncio
async def test_light_control_all_zones(homey_assistant):
    """Test light control for all zones."""
    input_data = {
        "intent": {
            "type": "light_control",
            "zone": "all",
            "value": "off"
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "Turning off all lights"
    assert len(result["actions"]) == 2
    assert all(action["value"] == "off" for action in result["actions"])
    assert result["needs_confirmation"] is True


@pytest.mark.asyncio
async def test_thermostat_control(homey_assistant):
    """Test thermostat control."""
    input_data = {
        "intent": {
            "type": "thermostat_control",
            "zone": "woonkamer",
            "value": 22.0
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "Setting temperature to 22.0°C in woonkamer"
    assert len(result["actions"]) == 1
    assert result["actions"][0]["device"] == "thermostat1"
    assert result["actions"][0]["action"] == "set"
    assert result["actions"][0]["value"] == 22.0
    assert result["needs_confirmation"] is True


@pytest.mark.asyncio
async def test_thermostat_control_no_device(homey_assistant):
    """Test thermostat control when no device exists."""
    input_data = {
        "intent": {
            "type": "thermostat_control",
            "zone": "keuken",
            "value": 22.0
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "No thermostat found in keuken"
    assert len(result["actions"]) == 0
    assert result["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_sensor_read(homey_assistant):
    """Test sensor reading."""
    input_data = {
        "intent": {
            "type": "sensor_read",
            "zone": "woonkamer"
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert "Current sensor readings for woonkamer:" in result["response"]
    assert "temperature_sensor: 21.5" in result["response"]
    assert len(result["actions"]) == 0
    assert result["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_unknown_intent(homey_assistant):
    """Test handling of unknown intent."""
    input_data = {
        "intent": {
            "type": "unknown",
            "zone": "woonkamer"
        }
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "I'm sorry, I didn't understand that command."
    assert len(result["actions"]) == 0
    assert result["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_empty_intent(homey_assistant):
    """Test handling of empty intent."""
    input_data = {
        "intent": {}
    }
    
    result = await homey_assistant.process(input_data)
    
    assert result["response"] == "I'm sorry, I didn't understand that command."
    assert len(result["actions"]) == 0
    assert result["needs_confirmation"] is False 