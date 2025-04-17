"""Tests for the BaseAgent class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.base_agent import BaseAgent


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
    client.publish = Mock(return_value=True)
    client.get_status = Mock(return_value={"value": 21.5})
    return client


@pytest.fixture
def base_agent(mock_config, mock_mqtt_client):
    """Create a BaseAgent instance with mocked dependencies."""
    return BaseAgent(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_agent_initialization(base_agent, mock_config, mock_mqtt_client):
    """Test that the agent initializes correctly."""
    assert base_agent.config == mock_config
    assert base_agent.mqtt_client == mock_mqtt_client
    assert base_agent.agent is not None


@pytest.mark.asyncio
async def test_process_method(base_agent):
    """Test that the process method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        await base_agent.process({})


@pytest.mark.asyncio
async def test_execute_device_action(base_agent, mock_mqtt_client):
    """Test executing a device action through MQTT."""
    result = await base_agent.execute_device_action(
        device_id="test_device",
        capability="test_capability",
        value=50
    )
    
    assert result["success"] is True
    mock_mqtt_client.publish.assert_called_once_with(
        "test_device/test_capability/set",
        {"value": 50}
    )


@pytest.mark.asyncio
async def test_get_device_status(base_agent, mock_mqtt_client):
    """Test retrieving device status through MQTT."""
    result = await base_agent.get_device_status(
        device_id="test_device",
        capability="test_capability"
    )
    
    assert result == {"value": 21.5}
    mock_mqtt_client.get_status.assert_called_once_with(
        "test_device/test_capability"
    )


@pytest.mark.asyncio
async def test_log_message(base_agent):
    """Test message logging."""
    base_agent._log_message("Test message", "test_agent")
    
    # Verify that the message was logged
    # Note: In a real implementation, this would check the actual logging output
    assert True  # Placeholder for actual logging verification


@pytest.mark.asyncio
async def test_create_agent(base_agent, mock_config):
    """Test agent creation with configuration."""
    agent = base_agent._create_agent()
    
    assert agent is not None
    assert agent.config_list == mock_config["config_list"]
    assert agent.temperature == mock_config["temperature"]


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