"""Tests for the HomeyAssistant class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.homey_assistant import HomeyAssistant


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
    return client


@pytest.fixture
def homey_assistant(mock_config, mock_mqtt_client):
    """Create a HomeyAssistant instance with mocked dependencies."""
    return HomeyAssistant(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_process_light_control(homey_assistant):
    """Test processing light control intent."""
    result = await homey_assistant.process({
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "actions" in result
    assert len(result["actions"]) == 1
    assert result["actions"][0]["device_id"] == "woonkamer_light"
    assert result["actions"][0]["capability"] == "onoff"
    assert result["actions"][0]["value"] == "on"
    assert not result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_temperature_control(homey_assistant):
    """Test processing temperature control intent."""
    result = await homey_assistant.process({
        "intent": {
            "type": "control",
            "device_type": "thermostat",
            "zone": "keuken",
            "value": 21,
            "confidence": 0.9
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "actions" in result
    assert len(result["actions"]) == 1
    assert result["actions"][0]["device_id"] == "keuken_thermostat"
    assert result["actions"][0]["capability"] == "target_temperature"
    assert result["actions"][0]["value"] == 21
    assert not result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_sensor_read(homey_assistant):
    """Test processing sensor read intent."""
    result = await homey_assistant.process({
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "slaapkamer",
            "confidence": 0.85
        },
        "sensor_data": {
            "temperature": {
                "value": 20.5,
                "unit": "°C"
            }
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "De temperatuur in de slaapkamer is 20.5°C" in result["response"]
    assert "actions" in result
    assert len(result["actions"]) == 0
    assert not result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_multiple_actions(homey_assistant):
    """Test processing intent requiring multiple actions."""
    result = await homey_assistant.process({
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "all",
            "value": "off",
            "confidence": 0.8
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "actions" in result
    assert len(result["actions"]) > 1
    assert all(action["capability"] == "onoff" for action in result["actions"])
    assert all(action["value"] == "off" for action in result["actions"])
    assert result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_low_confidence(homey_assistant):
    """Test processing intent with low confidence."""
    result = await homey_assistant.process({
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.3
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "actions" in result
    assert result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_invalid_intent(homey_assistant):
    """Test processing invalid intent."""
    result = await homey_assistant.process({
        "intent": {
            "type": "unknown",
            "confidence": 0.1
        }
    })
    
    assert result["status"] == "success"
    assert "response" in result
    assert "actions" in result
    assert len(result["actions"]) == 0
    assert not result["requires_confirmation"]


@pytest.mark.asyncio
async def test_process_llm_error(homey_assistant):
    """Test error handling in LLM processing."""
    with patch.object(homey_assistant, '_get_llm_response', side_effect=Exception("LLM error")):
        result = await homey_assistant.process({
            "intent": {
                "type": "control",
                "device_type": "light",
                "zone": "woonkamer",
                "value": "on",
                "confidence": 0.95
            }
        })
        
        assert result["status"] == "error"
        assert "LLM error" in result["error"]


@pytest.mark.asyncio
async def test_process_json_parse_error(homey_assistant):
    """Test handling of invalid JSON response."""
    with patch.object(homey_assistant, '_get_llm_response', return_value="invalid json"):
        result = await homey_assistant.process({
            "intent": {
                "type": "control",
                "device_type": "light",
                "zone": "woonkamer",
                "value": "on",
                "confidence": 0.95
            }
        })
        
        assert result["status"] == "error"
        assert "Failed to parse LLM response" in result["error"] 