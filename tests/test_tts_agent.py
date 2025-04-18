"""Tests for the TTSAgent class."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.tts_agent import TTSAgent
from app.core.config import LLMConfig, OpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-tts",
        openai=OpenAIConfig(
            model="test-model",
            api_type="openai",
            api_key="test-key"
        ),
        speakers=[
            {"id": "speaker1", "zone": "woonkamer"},
            {"id": "speaker2", "zone": "woonkamer"},
            {"id": "speaker3", "zone": "keuken"}
        ],
        default_volume=50,
        default_zone="woonkamer"
    )


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
    client = AsyncMock()
    client.publish = AsyncMock(return_value=True)
    return client


@pytest.fixture
def tts_agent(mock_config, mock_mqtt_client, mock_tts_config):
    """Create a TTSAgent instance with mocked dependencies."""
    return TTSAgent(mock_config, mock_mqtt_client, mock_tts_config)


@pytest.mark.asyncio
async def test_process_success(tts_agent):
    """Test successful TTS processing."""
    result = await tts_agent.process({
        "text": "Hello, how can I help you?",
        "zone": "woonkamer"
    })
    
    assert result["status"] == "success"
    assert "message" in result


@pytest.mark.asyncio
async def test_process_empty_text(tts_agent):
    """Test TTS processing with empty text."""
    result = await tts_agent.process({
        "text": ""
    })
    
    assert result["status"] == "error"
    assert "No text provided" in result["message"]


@pytest.mark.asyncio
async def test_process_invalid_zone(tts_agent):
    """Test TTS processing with invalid zone."""
    result = await tts_agent.process({
        "text": "Test",
        "zone": "invalid_zone"
    })
    
    assert result["status"] == "error"
    assert "No speakers available" in result["message"]


@pytest.mark.asyncio
async def test_process_default_zone(tts_agent):
    """Test TTS processing with default zone."""
    result = await tts_agent.process({
        "text": "Test"
    })
    
    assert result["status"] == "success"
    assert "message" in result


@pytest.mark.asyncio
async def test_process_with_volume(tts_agent):
    """Test TTS processing with custom volume."""
    result = await tts_agent.process({
        "text": "Test",
        "zone": "woonkamer",
        "volume": 75
    })
    
    assert result["status"] == "success"
    assert "message" in result


@pytest.mark.asyncio
async def test_process_error(tts_agent):
    """Test error handling in TTS processing."""
    # Setup mock to raise exception
    tts_agent._text_to_speech = AsyncMock(side_effect=Exception("TTS error"))
    
    result = await tts_agent.process({
        "text": "Test error"
    })
    
    assert result["status"] == "error"
    assert "TTS error" in result["message"] 