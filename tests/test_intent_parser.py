"""Tests for the IntentParser."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.intent_parser import IntentParser
from app.core.config import LLMConfig, OpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="intent-parser",
        openai=OpenAIConfig(
            model="test-model",
            api_type="openai",
            api_key="test-key",
            zones=["woonkamer", "keuken", "slaapkamer"]
        )
    )


@pytest.fixture
def intent_parser(mock_config):
    """Create an IntentParser instance with mock dependencies."""
    return IntentParser(config=mock_config)


def test_light_control_intent(intent_parser):
    """Test parsing light control intent."""
    result = intent_parser.process({"message": "turn on the light in the woonkamer"})
    
    assert result["intent"]["type"] == "light_control"
    assert result["intent"]["zone"] == "woonkamer"
    assert result["intent"]["value"] == "on"
    assert result["intent"]["confidence"] >= 0.8


def test_thermostat_control_intent(intent_parser):
    """Test parsing thermostat control intent."""
    result = intent_parser.process({"message": "set temperature to 21 in woonkamer"})
    
    assert result["intent"]["type"] == "thermostat_control"
    assert result["intent"]["zone"] == "woonkamer"
    assert result["intent"]["value"] == 21.0
    assert result["intent"]["confidence"] >= 0.8


def test_sensor_read_intent(intent_parser):
    """Test parsing sensor read intent."""
    result = intent_parser.process({"message": "what's the sensor reading in woonkamer"})
    
    assert result["intent"]["type"] == "sensor_read"
    assert result["intent"]["zone"] == "woonkamer"
    assert result["intent"]["confidence"] >= 0.7


def test_all_lights_intent(intent_parser):
    """Test parsing all lights control intent."""
    result = intent_parser.process({"message": "turn on all lights"})
    
    assert result["intent"]["type"] == "light_control"
    assert result["intent"]["zone"] == "all"
    assert result["intent"]["value"] == "on"
    assert result["intent"]["confidence"] >= 0.9


def test_unknown_intent(intent_parser):
    """Test parsing unknown intent."""
    result = intent_parser.process({"message": "play some music"})
    
    assert result["intent"]["type"] == "unknown"
    assert result["intent"]["confidence"] <= 0.5


def test_empty_message(intent_parser):
    """Test parsing empty message."""
    result = intent_parser.process({"message": ""})
    
    assert result["intent"]["type"] == "unknown"
    assert result["intent"]["confidence"] <= 0.5


def test_zone_extraction(intent_parser):
    """Test zone extraction from message."""
    result = intent_parser.process({"message": "turn on the light in the keuken"})
    
    assert result["intent"]["zone"] == "keuken"


def test_default_zone(intent_parser):
    """Test default zone when none specified."""
    result = intent_parser.process({"message": "turn on the light"})
    
    assert result["intent"]["zone"] == "woonkamer" 