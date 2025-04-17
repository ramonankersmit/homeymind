"""Tests for the IntentParser."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.intent_parser import IntentParser


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "name": "intent-parser",
        "system_message": "You are an intent parsing assistant.",
        "config_list": [{"model": "test-model"}],
        "temperature": 0.7,
        "zones": ["woonkamer", "keuken", "slaapkamer", "badkamer"],
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
def intent_parser(mock_config, mock_mqtt_client):
    """Create an IntentParser instance with mock dependencies."""
    return IntentParser(
        config=mock_config,
        mqtt_client=mock_mqtt_client
    )


@pytest.mark.asyncio
async def test_light_control_intent(intent_parser):
    """Test parsing light control intent."""
    message = "zet het licht aan in de woonkamer"
    result = await intent_parser.process({"message": message})
    
    assert result["type"] == "light_control"
    assert result["device_type"] == "light"
    assert result["zone"] == "woonkamer"
    assert result["value"] == "on"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_thermostat_control_intent(intent_parser):
    """Test parsing thermostat control intent."""
    message = "zet de temperatuur op 21 graden in de woonkamer"
    result = await intent_parser.process({"message": message})
    
    assert result["type"] == "thermostat_control"
    assert result["device_type"] == "thermostat"
    assert result["zone"] == "woonkamer"
    assert result["value"] == 21
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_sensor_read_intent(intent_parser):
    """Test parsing sensor read intent."""
    message = "wat is de temperatuur in de woonkamer"
    result = await intent_parser.process({"message": message})
    
    assert result["type"] == "sensor_read"
    assert result["device_type"] == "temperature_sensor"
    assert result["zone"] == "woonkamer"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_all_lights_intent(intent_parser):
    """Test parsing all lights control intent."""
    message = "zet alle lichten uit"
    result = await intent_parser.process({"message": message})
    
    assert result["type"] == "light_control"
    assert result["device_type"] == "light"
    assert result["zone"] == "all"
    assert result["value"] == "off"
    assert result["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_unknown_intent(intent_parser):
    """Test parsing unknown intent."""
    message = "vertel me een verhaal"
    result = await intent_parser.process({"message": message})
    
    assert result["type"] == "unknown"
    assert result["confidence"] <= 0.3


@pytest.mark.asyncio
async def test_empty_message(intent_parser):
    """Test handling empty message."""
    result = await intent_parser.process({"message": ""})
    
    assert result["type"] == "unknown"
    assert result["confidence"] == 0.0


@pytest.mark.asyncio
async def test_zone_extraction(intent_parser):
    """Test zone extraction from message."""
    message = "zet het licht aan in de keuken"
    result = await intent_parser.process({"message": message})
    
    assert result["zone"] == "keuken"


@pytest.mark.asyncio
async def test_default_zone(intent_parser):
    """Test default zone when none specified."""
    message = "zet het licht aan"
    result = await intent_parser.process({"message": message})
    
    assert result["zone"] == "woonkamer"  # Default zone 