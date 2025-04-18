"""Tests for the AutoGenManager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.autogen_manager import AutoGenManager
from app.core.config import LLMConfig, OpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-agent",
        openai=OpenAIConfig(
            model="test-model",
            api_type="openai",
            api_key="test-key"
        ),
        mqtt_config={
            "host": "localhost",
            "port": 1883
        },
        tts_config={
            "voice": "nl-NL-Standard-A",
            "audio_device": "default"
        },
        llm_config={},
        require_confirmation=True
    )


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
    client.connect = MagicMock()  # Use MagicMock for sync methods
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
    """Test successful intent processing."""
    # Configure mock responses
    intent_result = {
        "status": "success",
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    }
    mock_agents["intent_parser"].process.return_value = intent_result
    
    assistant_result = {
        "status": "success",
        "response": "I'll turn on the light.",
        "actions": []
    }
    mock_agents["homey_assistant"].process.return_value = assistant_result
    
    tts_result = {
        "status": "success",
        "message": "TTS enqueued"
    }
    mock_agents["tts_agent"].process.return_value = tts_result
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Turn on the light")
    
    # Verify success result
    assert result["status"] == "success"
    assert result["response"] == "I'll turn on the light."
    assert len(result["actions"]) == 0


@pytest.mark.asyncio
async def test_process_intent_streaming_sensor_data(autogen_manager, mock_agents):
    """Test intent processing with sensor data."""
    # Configure mock responses
    intent_result = {
        "status": "success",
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    }
    mock_agents["intent_parser"].process.return_value = intent_result
    
    sensor_result = {
        "status": "success",
        "response": "Temperature is 22.5°C"
    }
    mock_agents["sensor_agent"].process.return_value = sensor_result
    
    assistant_result = {
        "status": "success",
        "response": "Temperature is 22.5°C",
        "actions": []
    }
    mock_agents["homey_assistant"].process.return_value = assistant_result
    
    tts_result = {
        "status": "success",
        "message": "TTS enqueued"
    }
    mock_agents["tts_agent"].process.return_value = tts_result
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("What's the temperature?")
    
    # Verify success result
    assert result["status"] == "success"
    assert result["response"] == "Temperature is 22.5°C"
    assert len(result["actions"]) == 0


@pytest.mark.asyncio
async def test_process_intent_streaming_error(autogen_manager, mock_agents):
    """Test error handling during intent processing."""
    # Configure mock to raise exception
    mock_agents["intent_parser"].process.side_effect = Exception("Intent parsing failed")
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Invalid input")
    
    # Verify error result
    assert result["status"] == "error"
    assert result["error"] == "Intent parsing failed"


@pytest.mark.asyncio
async def test_process_intent_streaming_sensor_error(autogen_manager, mock_agents):
    """Test error handling during sensor processing."""
    # Configure mock responses
    intent_result = {
        "status": "success",
        "intent": {
            "type": "read_sensor",
            "device_type": "temperature",
            "zone": "woonkamer"
        }
    }
    mock_agents["intent_parser"].process.return_value = intent_result
    
    sensor_result = {
        "status": "error",
        "error": "Sensor not responding"
    }
    mock_agents["sensor_agent"].process.return_value = sensor_result
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("What's the temperature?")
    
    # Verify error result
    assert result["status"] == "error"
    assert result["error"] == "Sensor not responding"


@pytest.mark.asyncio
async def test_process_intent_streaming_tts_error(autogen_manager, mock_agents):
    """Test error handling during TTS processing."""
    # Configure mock responses
    intent_result = {
        "status": "success",
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    }
    mock_agents["intent_parser"].process.return_value = intent_result
    
    assistant_result = {
        "status": "success",
        "response": "I'll turn on the light.",
        "actions": []
    }
    mock_agents["homey_assistant"].process.return_value = assistant_result
    
    tts_result = {
        "status": "error",
        "error": "TTS service unavailable"
    }
    mock_agents["tts_agent"].process.return_value = tts_result
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Turn on the light")
    
    # Verify error result
    assert result["status"] == "error"
    assert result["error"] == "TTS service unavailable"


@pytest.mark.asyncio
async def test_process_intent_streaming_device_error(autogen_manager, mock_agents):
    """Test error handling during device control."""
    # Configure mock responses
    intent_result = {
        "status": "success",
        "intent": {
            "type": "control",
            "device_type": "light",
            "zone": "woonkamer",
            "value": "on",
            "confidence": 0.95
        }
    }
    mock_agents["intent_parser"].process.return_value = intent_result
    
    assistant_result = {
        "status": "success",
        "response": "I'll turn on the light.",
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff",
                "value": "on"
            }
        ]
    }
    mock_agents["homey_assistant"].process.return_value = assistant_result
    
    device_result = {
        "status": "error",
        "error": "Device not responding"
    }
    mock_agents["device_controller"].process.return_value = device_result
    
    tts_result = {
        "status": "success",
        "message": "TTS enqueued"
    }
    mock_agents["tts_agent"].process.return_value = tts_result
    
    # Process intent
    result = await autogen_manager.process_intent_streaming("Turn on the light")
    
    # Verify error result
    assert result["status"] == "error"
    assert result["error"] == "Device not responding"


@pytest.mark.asyncio
async def test_close(autogen_manager, mock_mqtt_client):
    """Test proper cleanup of resources."""
    await autogen_manager.close()
    mock_mqtt_client.disconnect.assert_called_once() 