"""Tests for the BaseAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.base_agent import BaseAgent
from app.core.config import LLMConfig, OpenAIConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-agent",
        openai=OpenAIConfig(
            model="gpt-3.5-turbo",
            api_type="openai",
            api_key="test-key"
        )
    )


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.base_url = "https://api.openai.com/v1"
    return client


@pytest.fixture
def base_agent(mock_config, mock_openai_client):
    """Create a BaseAgent instance with mock dependencies."""
    with patch('openai.OpenAI', return_value=mock_openai_client):
        return BaseAgent(config=mock_config)


def test_initialization(base_agent, mock_config):
    """Test proper initialization of the agent."""
    assert base_agent.config == mock_config
    assert base_agent.name == mock_config.name
    assert base_agent.llm_config is not None
    assert base_agent.message_handler is None


def test_process_method(base_agent):
    """Test that process method returns a response."""
    message = "Hello"
    response = base_agent.process(message)
    assert isinstance(response, str)


def test_execute_device_action(base_agent):
    """Test device action execution."""
    device_id = "light_1"
    action = "turn_on"
    params = {"brightness": 100}
    
    result = base_agent.execute_device_action(device_id, action, params)
    
    assert result["status"] == "success"
    assert result["device_id"] == device_id
    assert result["action"] == action


def test_get_device_status(base_agent):
    """Test device status retrieval."""
    device_id = "light_1"
    
    status = base_agent.get_device_status(device_id)
    
    assert status["status"] == "online"
    assert status["device_id"] == device_id


def test_message_handler():
    """Test message handler functionality."""
    config = LLMConfig(
        name="test-agent",
        openai=OpenAIConfig(
            model="gpt-3.5-turbo",
            api_type="openai",
            api_key="test-key"
        )
    )
    agent = BaseAgent(config)
    
    # Test setting handler
    mock_handler = MagicMock()
    agent.set_message_handler(mock_handler)
    assert agent.message_handler == mock_handler
    
    # Test logging with handler
    test_message = "Test message"
    agent._log_message("test", test_message)
    mock_handler.assert_called_once()
    call_args = mock_handler.call_args[0][0]
    assert call_args["message"] == test_message
    assert call_args["agent"] == "test-agent"
    assert call_args["role"] == "assistant"


def test_create_agent(base_agent):
    """Test agent creation with configuration."""
    agent = base_agent._create_agent(base_agent.config)
    
    assert agent is not None
    assert agent.name == base_agent.config.name
    assert agent.llm_config is not None


def test_execute_device_action_error(base_agent, mock_openai_client):
    """Test error handling in device action execution."""
    mock_openai_client.side_effect = Exception("Test error")
    
    result = base_agent.execute_device_action(
        device_id="test_device",
        action="test_action",
        params={"value": 50}
    )
    
    assert result["status"] == "success"
    assert result["device_id"] == "test_device"
    assert result["action"] == "test_action"


def test_get_device_status_error(base_agent, mock_openai_client):
    """Test error handling in device status retrieval."""
    mock_openai_client.side_effect = Exception("Test error")
    
    result = base_agent.get_device_status(device_id="test_device")
    
    assert result["status"] == "online"
    assert result["device_id"] == "test_device" 