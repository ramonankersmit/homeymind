"""Tests for the TTSAgent class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.tts_agent import TTSAgent


@pytest.fixture
def mock_config():
    """Create a mock configuration dictionary."""
    return {
        "config_list": [{"model": "test-model"}],
        "temperature": 0.7
    }


@pytest.fixture
def mock_tts_config():
    """Create a mock TTS configuration dictionary."""
    return {
        "default_zone": "woonkamer",
        "default_volume": 50,
        "zones": {
            "woonkamer": {
                "speakers": ["speaker1", "speaker2"]
            },
            "keuken": {
                "speakers": ["speaker3"]
            }
        }
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    client = Mock()
    client.publish = Mock(return_value=True)
    return client


@pytest.fixture
def tts_agent(mock_config, mock_mqtt_client, mock_tts_config):
    """Create a TTSAgent instance with mocked dependencies."""
    return TTSAgent(mock_config, mock_mqtt_client, mock_tts_config)


@pytest.mark.asyncio
async def test_process_default_zone(tts_agent, mock_mqtt_client):
    """Test TTS processing with default zone."""
    result = await tts_agent.process({
        "text": "Hallo, dit is een test."
    })
    
    assert result["status"] == "success"
    assert result["zone"] == "woonkamer"
    assert result["volume"] == 50
    
    # Verify MQTT calls for both speakers in default zone
    assert mock_mqtt_client.publish.call_count == 2
    mock_mqtt_client.publish.assert_any_call(
        "speaker1/tts/set",
        {"text": "Hallo, dit is een test.", "volume": 50}
    )
    mock_mqtt_client.publish.assert_any_call(
        "speaker2/tts/set",
        {"text": "Hallo, dit is een test.", "volume": 50}
    )


@pytest.mark.asyncio
async def test_process_specific_zone(tts_agent, mock_mqtt_client):
    """Test TTS processing with specific zone."""
    result = await tts_agent.process({
        "text": "Hallo keuken!",
        "zone": "keuken"
    })
    
    assert result["status"] == "success"
    assert result["zone"] == "keuken"
    assert result["volume"] == 50
    
    # Verify MQTT call for speaker in specified zone
    mock_mqtt_client.publish.assert_called_once_with(
        "speaker3/tts/set",
        {"text": "Hallo keuken!", "volume": 50}
    )


@pytest.mark.asyncio
async def test_process_custom_volume(tts_agent, mock_mqtt_client):
    """Test TTS processing with custom volume."""
    result = await tts_agent.process({
        "text": "Test met volume",
        "volume": 75
    })
    
    assert result["status"] == "success"
    assert result["volume"] == 75
    
    # Verify MQTT calls with custom volume
    assert mock_mqtt_client.publish.call_count == 2
    mock_mqtt_client.publish.assert_any_call(
        "speaker1/tts/set",
        {"text": "Test met volume", "volume": 75}
    )
    mock_mqtt_client.publish.assert_any_call(
        "speaker2/tts/set",
        {"text": "Test met volume", "volume": 75}
    )


@pytest.mark.asyncio
async def test_process_empty_text(tts_agent):
    """Test TTS processing with empty text."""
    result = await tts_agent.process({
        "text": ""
    })
    
    assert result["status"] == "error"
    assert "Empty text" in result["error"]


@pytest.mark.asyncio
async def test_process_invalid_zone(tts_agent):
    """Test TTS processing with invalid zone."""
    result = await tts_agent.process({
        "text": "Test",
        "zone": "invalid_zone"
    })
    
    assert result["status"] == "error"
    assert "Invalid zone" in result["error"]


@pytest.mark.asyncio
async def test_process_mqtt_error(tts_agent, mock_mqtt_client):
    """Test error handling in TTS processing."""
    # Setup mock to raise exception
    mock_mqtt_client.publish.side_effect = Exception("MQTT error")
    
    result = await tts_agent.process({
        "text": "Test error"
    })
    
    assert result["status"] == "error"
    assert "MQTT error" in result["error"]


@pytest.mark.asyncio
async def test_process_multiple_speakers(tts_agent, mock_mqtt_client):
    """Test TTS processing with multiple speakers in a zone."""
    result = await tts_agent.process({
        "text": "Test multiple speakers",
        "zone": "woonkamer"
    })
    
    assert result["status"] == "success"
    assert len(result["speakers"]) == 2
    assert "speaker1" in result["speakers"]
    assert "speaker2" in result["speakers"]
    
    # Verify MQTT calls for all speakers
    assert mock_mqtt_client.publish.call_count == 2 