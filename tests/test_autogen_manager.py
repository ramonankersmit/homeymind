"""Tests for the AutoGenManager class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.autogen_manager import AutoGenManager


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "llm_config": {
            "config_list": [{"model": "test-model"}],
            "temperature": 0.7
        },
        "mqtt_config": {
            "host": "localhost",
            "port": 1883
        },
        "tts_config": {
            "default_zone": "woonkamer",
            "default_volume": 50
        }
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    client = Mock()
    client.connect = Mock()
    client.disconnect = Mock()
    return client


@pytest.fixture
def mock_agents():
    """Create mock agent instances."""
    return {
        "sensor": Mock(),
        "intent_parser": Mock(),
        "assistant": Mock(),
        "tts": Mock(),
        "device_controller": Mock()
    }


@pytest.fixture
def autogen_manager(mock_config, mock_mqtt_client, mock_agents):
    """Create an AutoGenManager instance with mocked dependencies."""
    with patch("app.agents.autogen_manager.HomeyMQTTClient", return_value=mock_mqtt_client), \
         patch("app.agents.autogen_manager.SensorAgent", return_value=mock_agents["sensor"]), \
         patch("app.agents.autogen_manager.IntentParser", return_value=mock_agents["intent_parser"]), \
         patch("app.agents.autogen_manager.HomeyAssistant", return_value=mock_agents["assistant"]), \
         patch("app.agents.autogen_manager.TTSAgent", return_value=mock_agents["tts"]), \
         patch("app.agents.autogen_manager.DeviceController", return_value=mock_agents["device_controller"]):
        manager = AutoGenManager(mock_config)
        return manager


@pytest.mark.asyncio
async def test_initialization(autogen_manager, mock_config, mock_mqtt_client):
    """Test that the manager initializes correctly."""
    assert autogen_manager.config == mock_config
    assert autogen_manager.mqtt_client == mock_mqtt_client
    assert mock_mqtt_client.connect.called


@pytest.mark.asyncio
async def test_process_intent_streaming_success(autogen_manager, mock_agents):
    """Test successful intent processing flow."""
    # Setup mock responses
    mock_agents["intent_parser"].process.return_value = {
        "intent": {
            "type": "set_brightness",
            "device_type": "light",
            "zone": "woonkamer",
            "value": 80
        },
        "confidence": 0.95
    }
    
    mock_agents["assistant"].process.return_value = {
        "response": "Ik zal de lampen in de woonkamer op 80% zetten.",
        "actions": [{
            "device_id": "woonkamer_lamp",
            "capability": "brightness",
            "value": 80
        }],
        "requires_confirmation": False
    }
    
    mock_agents["tts"].process.return_value = {"status": "success"}
    mock_agents["device_controller"].process.return_value = {
        "status": "success",
        "executed_actions": [{
            "device_id": "woonkamer_lamp",
            "capability": "brightness",
            "value": 80,
            "status": "success"
        }]
    }
    
    # Process intent
    result = await autogen_manager.process_intent_streaming(
        "Zet de lampen in de woonkamer op 80%"
    )
    
    # Verify result
    assert result["status"] == "success"
    assert "intent" in result["data"]
    assert "response" in result["data"]
    assert "actions" in result["data"]
    
    # Verify agent calls
    mock_agents["intent_parser"].process.assert_called_once()
    mock_agents["assistant"].process.assert_called_once()
    mock_agents["tts"].process.assert_called_once()
    mock_agents["device_controller"].process.assert_called_once()


@pytest.mark.asyncio
async def test_process_intent_streaming_sensor_data(autogen_manager, mock_agents):
    """Test intent processing with sensor data retrieval."""
    # Setup mock responses
    mock_agents["intent_parser"].process.return_value = {
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer"
        },
        "confidence": 0.95
    }
    
    mock_agents["sensor"].process.return_value = {
        "temperature": {
            "value": 21.5,
            "zone": "woonkamer",
            "unit": "°C"
        }
    }
    
    mock_agents["assistant"].process.return_value = {
        "response": "De temperatuur in de woonkamer is 21.5°C.",
        "actions": [],
        "requires_confirmation": False
    }
    
    # Process intent
    result = await autogen_manager.process_intent_streaming(
        "Wat is de temperatuur in de woonkamer?"
    )
    
    # Verify result
    assert result["status"] == "success"
    assert "sensor_data" in result["data"]
    assert result["data"]["sensor_data"]["temperature"]["value"] == 21.5
    
    # Verify agent calls
    mock_agents["sensor"].process.assert_called_once()


@pytest.mark.asyncio
async def test_process_intent_streaming_error(autogen_manager, mock_agents):
    """Test error handling during intent processing."""
    # Setup mock to raise exception
    mock_agents["intent_parser"].process.side_effect = Exception("Test error")
    
    # Process intent
    result = await autogen_manager.process_intent_streaming(
        "Zet de lampen aan"
    )
    
    # Verify error handling
    assert result["status"] == "error"
    assert "error" in result
    assert result["error"] == "Test error"


@pytest.mark.asyncio
async def test_close(autogen_manager, mock_mqtt_client, mock_agents):
    """Test cleanup on close."""
    await autogen_manager.close()
    
    # Verify cleanup
    mock_mqtt_client.disconnect.assert_called_once()
    for agent in mock_agents.values():
        if hasattr(agent, "close"):
            agent.close.assert_called_once() 