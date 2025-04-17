"""Tests for the BaseAgent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.base_agent import BaseAgent


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "name": "test-agent",
        "system_message": "Test system message",
        "config_list": [{"model": "test-model"}],
        "temperature": 0.7
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    return AsyncMock()


@pytest.fixture
def base_agent(mock_config, mock_mqtt_client):
    """Create a BaseAgent instance with mock dependencies."""
    return BaseAgent(
        config=mock_config,
        mqtt_client=mock_mqtt_client
    )


@pytest.mark.asyncio
async def test_initialization(base_agent, mock_config, mock_mqtt_client):
    """Test proper initialization of the agent."""
    assert base_agent.config == mock_config
    assert base_agent.mqtt_client == mock_mqtt_client
    assert base_agent.llm_config["config_list"] == mock_config["config_list"]
    assert base_agent.llm_config["temperature"] == mock_config["temperature"]
    assert base_agent.message_handler is None


@pytest.mark.asyncio
async def test_process_method(base_agent):
    """Test that process method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await base_agent.process({})


@pytest.mark.asyncio
async def test_execute_device_action(base_agent, mock_mqtt_client):
    """Test device action execution through MQTT."""
    device_id = "light_1"
    capability = "onoff"
    value = "on"
    
    result = await base_agent.execute_device_action(device_id, capability, value)
    
    assert result["success"] is True
    mock_mqtt_client.publish.assert_called_once_with(
        f"device/{device_id}/{capability}/set",
        {"value": value}
    )


@pytest.mark.asyncio
async def test_get_device_status(base_agent, mock_mqtt_client):
    """Test device status retrieval through MQTT."""
    device_id = "light_1"
    capability = "onoff"
    mock_mqtt_client.get_status.return_value = "on"
    
    status = await base_agent.get_device_status(device_id, capability)
    
    assert status == "on"
    mock_mqtt_client.get_status.assert_called_once_with(
        f"device/{device_id}/{capability}"
    )


@pytest.mark.asyncio
async def test_message_handler():
    """Test message handler functionality."""
    mock_config = {"name": "test-agent"}
    mock_mqtt_client = AsyncMock()
    agent = BaseAgent(mock_config, mock_mqtt_client)
    
    # Test setting handler
    mock_handler = MagicMock()
    agent.set_message_handler(mock_handler)
    assert agent.message_handler == mock_handler
    
    # Test logging with handler
    test_message = "Test message"
    with patch('logging.getLogger') as mock_logger:
        agent._log_message(test_message)
        mock_handler.assert_called_once()
        call_args = mock_handler.call_args[0][0]
        assert call_args["message"] == test_message
        assert call_args["agent"] == "test-agent"
        assert call_args["role"] == "assistant"
    
    # Test clearing handler
    agent.clear_message_handler()
    assert agent.message_handler is None


@pytest.mark.asyncio
async def test_create_agent(base_agent):
    """Test agent creation with configuration."""
    agent = base_agent._create_agent()
    
    assert agent is not None
    assert agent.name == base_agent.config["name"]
    assert agent.system_message == base_agent.config["system_message"]
    
    # Check LLMConfig values instead of comparing objects
    assert agent.llm_config.temperature == base_agent.llm_config["temperature"]
    assert len(agent.llm_config.config_list) == len(base_agent.llm_config["config_list"])
    assert agent.llm_config.config_list[0]["model"] == base_agent.llm_config["config_list"][0]["model"]


@pytest.mark.asyncio
async def test_execute_device_action_error(base_agent, mock_mqtt_client):
    """Test error handling in device action execution."""
    mock_mqtt_client.publish.side_effect = Exception("Test error")
    
    result = await base_agent.execute_device_action(
        device_id="test_device",
        capability="test_capability",
        value=50
    )
    
    assert result["success"] is False
    assert "error" in result
    assert result["error"] == "Test error"


@pytest.mark.asyncio
async def test_get_device_status_error(base_agent, mock_mqtt_client):
    """Test error handling in device status retrieval."""
    mock_mqtt_client.get_status.side_effect = Exception("Test error")
    
    result = await base_agent.get_device_status(
        device_id="test_device",
        capability="test_capability"
    )
    
    assert result == {"error": "Test error"} 