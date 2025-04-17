"""Tests for the AutoGenManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.autogen_manager import AutoGenManager


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "mqtt_config": {
            "host": "localhost",
            "port": 1883
        },
        "tts_config": {
            "voice": "nl-NL-Standard-A",
            "audio_device": "default"
        },
        "llm_config": {},
        "require_confirmation": True
    }


@pytest.fixture
def mock_agents():
    """Create mock agent instances."""
    return {
        "intent_parser": AsyncMock(),
        "sensor_agent": AsyncMock(),
        "homey_assistant": AsyncMock(),
        "tts_agent": AsyncMock(),
        "device_controller": AsyncMock()
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    client = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    return client


@pytest.fixture
def autogen_manager(mock_config, mock_agents, mock_mqtt_client):
    """Create an AutoGenManager instance with mock dependencies."""
    with patch("app.agents.autogen_manager.HomeyMQTTClient", return_value=mock_mqtt_client), \
         patch("app.agents.autogen_manager.IntentParser", return_value=mock_agents["intent_parser"]), \
         patch("app.agents.autogen_manager.SensorAgent", return_value=mock_agents["sensor_agent"]), \
         patch("app.agents.autogen_manager.HomeyAssistant", return_value=mock_agents["homey_assistant"]), \
         patch("app.agents.autogen_manager.TTSAgent", return_value=mock_agents["tts_agent"]), \
         patch("app.agents.autogen_manager.DeviceController", return_value=mock_agents["device_controller"]):
        return AutoGenManager(mock_config)


@pytest.mark.asyncio
async def test_initialization(autogen_manager, mock_mqtt_client, mock_agents):
    """Test proper initialization of manager and agents."""
    # Verify MQTT client initialization
    mock_mqtt_client.connect.assert_called_once()
    
    # Verify agent initialization
    assert autogen_manager.mqtt_client == mock_mqtt_client
    assert autogen_manager.intent_parser == mock_agents["intent_parser"]
    assert autogen_manager.sensor_agent == mock_agents["sensor_agent"]
    assert autogen_manager.homey_assistant == mock_agents["homey_assistant"]
    assert autogen_manager.tts_agent == mock_agents["tts_agent"]
    assert autogen_manager.device_controller == mock_agents["device_controller"]


@pytest.mark.asyncio
async def test_process_intent_streaming_success(autogen_manager, mock_agents):
    """Test successful intent processing flow."""
    # Configure mock responses
    mock_agents["intent_parser"].process.return_value = {
        "status": "success",
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    }
    
    mock_agents["homey_assistant"].process.return_value = {
        "status": "success",
        "response": "I'll turn on the light in the woonkamer.",
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    }
    
    mock_agents["device_controller"].process.return_value = {
        "status": "success",
        "results": [
            {
                "device_id": "light_1",
                "status": "success",
                "message": "Light turned on"
            }
        ]
    }
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Turn on the light in the woonkamer")
    
    # Verify result
    assert result["status"] == "success"
    assert "intent" in result["data"]
    assert "response" in result["data"]
    assert "actions" in result["data"]
    
    # Verify agent calls
    mock_agents["intent_parser"].process.assert_called_once()
    mock_agents["homey_assistant"].process.assert_called_once()
    mock_agents["device_controller"].process.assert_called_once()
    mock_agents["tts_agent"].process.assert_called_once()


@pytest.mark.asyncio
async def test_process_intent_streaming_sensor_data(autogen_manager, mock_agents):
    """Test intent processing with sensor data retrieval."""
    # Configure mock responses
    mock_agents["intent_parser"].process.return_value = {
        "status": "success",
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer",
            "confidence": 0.95
        }
    }
    
    mock_agents["sensor_agent"].process.return_value = {
        "status": "success",
        "sensor_data": {
            "type": "temperature",
            "zone": "woonkamer",
            "value": 22.5,
            "timestamp": "2024-03-20T10:00:00"
        }
    }
    
    mock_agents["homey_assistant"].process.return_value = {
        "status": "success",
        "response": "The temperature in the woonkamer is 22.5°C.",
        "actions": [],
        "requires_confirmation": False
    }
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("What's the temperature in the woonkamer?")
    
    # Verify result
    assert result["status"] == "success"
    assert "sensor_data" in result["data"]
    assert result["data"]["sensor_data"]["value"] == 22.5
    
    # Verify agent calls
    mock_agents["sensor_agent"].process.assert_called_once()
    mock_agents["device_controller"].process.assert_not_called()


@pytest.mark.asyncio
async def test_process_intent_streaming_error(autogen_manager, mock_agents):
    """Test error handling during intent processing."""
    # Configure mock to raise exception
    mock_agents["intent_parser"].process.side_effect = Exception("Intent parsing failed")
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Invalid input")
    
    # Verify error result
    assert result["status"] == "error"
    assert "Failed to process intent" in result["error"]
    
    # Verify no further agent calls
    mock_agents["sensor_agent"].process.assert_not_called()
    mock_agents["homey_assistant"].process.assert_not_called()
    mock_agents["device_controller"].process.assert_not_called()
    mock_agents["tts_agent"].process.assert_not_called()


@pytest.mark.asyncio
async def test_close(autogen_manager, mock_mqtt_client):
    """Test proper cleanup of resources."""
    await autogen_manager.close()
    mock_mqtt_client.disconnect.assert_called_once() 