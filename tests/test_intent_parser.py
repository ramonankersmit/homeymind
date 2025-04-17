"""Tests for the IntentParser class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.intent_parser import IntentParser


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
def intent_parser(mock_config, mock_mqtt_client):
    """Create an IntentParser instance with mocked dependencies."""
    return IntentParser(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_process_light_control(intent_parser):
    """Test parsing light control intent."""
    result = await intent_parser.process({
        "message": "Zet het licht in de woonkamer aan"
    })
    
    assert result["status"] == "success"
    assert result["intent"]["type"] == "control"
    assert result["intent"]["device_type"] == "light"
    assert result["intent"]["zone"] == "woonkamer"
    assert result["intent"]["value"] == "on"
    assert 0 <= result["intent"]["confidence"] <= 1


@pytest.mark.asyncio
async def test_process_temperature_control(intent_parser):
    """Test parsing temperature control intent."""
    result = await intent_parser.process({
        "message": "Zet de temperatuur in de keuken op 21 graden"
    })
    
    assert result["status"] == "success"
    assert result["intent"]["type"] == "control"
    assert result["intent"]["device_type"] == "thermostat"
    assert result["intent"]["zone"] == "keuken"
    assert result["intent"]["value"] == 21
    assert 0 <= result["intent"]["confidence"] <= 1


@pytest.mark.asyncio
async def test_process_sensor_read(intent_parser):
    """Test parsing sensor read intent."""
    result = await intent_parser.process({
        "message": "Wat is de temperatuur in de slaapkamer?"
    })
    
    assert result["status"] == "success"
    assert result["intent"]["type"] == "read_sensor"
    assert result["intent"]["device_type"] == "temperature"
    assert result["intent"]["zone"] == "slaapkamer"
    assert result["intent"]["value"] is None
    assert 0 <= result["intent"]["confidence"] <= 1


@pytest.mark.asyncio
async def test_process_multiple_devices(intent_parser):
    """Test parsing intent with multiple devices."""
    result = await intent_parser.process({
        "message": "Doe alle lichten in huis uit"
    })
    
    assert result["status"] == "success"
    assert result["intent"]["type"] == "control"
    assert result["intent"]["device_type"] == "light"
    assert result["intent"]["zone"] == "all"
    assert result["intent"]["value"] == "off"
    assert 0 <= result["intent"]["confidence"] <= 1


@pytest.mark.asyncio
async def test_process_empty_message(intent_parser):
    """Test parsing empty message."""
    result = await intent_parser.process({
        "message": ""
    })
    
    assert result["status"] == "error"
    assert "Empty message" in result["error"]


@pytest.mark.asyncio
async def test_process_invalid_intent(intent_parser):
    """Test parsing invalid intent."""
    result = await intent_parser.process({
        "message": "Dit is een ongeldige opdracht"
    })
    
    assert result["status"] == "success"
    assert result["intent"]["type"] == "unknown"
    assert result["intent"]["confidence"] < 0.5


@pytest.mark.asyncio
async def test_process_llm_error(intent_parser):
    """Test error handling in LLM processing."""
    with patch.object(intent_parser, '_get_llm_response', side_effect=Exception("LLM error")):
        result = await intent_parser.process({
            "message": "Test error"
        })
        
        assert result["status"] == "error"
        assert "LLM error" in result["error"]


@pytest.mark.asyncio
async def test_process_json_parse_error(intent_parser):
    """Test handling of invalid JSON response."""
    with patch.object(intent_parser, '_get_llm_response', return_value="invalid json"):
        result = await intent_parser.process({
            "message": "Test parse error"
        })
        
        assert result["status"] == "success"
        assert result["intent"]["type"] == "unknown"
        assert result["intent"]["confidence"] == 0.0 