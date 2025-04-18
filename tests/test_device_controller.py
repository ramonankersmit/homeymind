"""Tests for the DeviceController."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.agents.device_controller import DeviceController
from app.core.config import LLMConfig, OpenAIConfig, Device


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return LLMConfig(
        name="test-device-controller",
        openai=OpenAIConfig(
            model="gpt-3.5-turbo",
            api_type="openai",
            api_key="test-key",
            devices=[
                Device(id="light_1", type="light", zone="woonkamer"),
                Device(id="thermostat_1", type="thermostat", zone="woonkamer")
            ]
        )
    )


@pytest.fixture
def device_controller(mock_config):
    """Create a DeviceController instance with mock dependencies."""
    return DeviceController(config=mock_config)


def test_process_single_action(device_controller):
    """Test processing a single device action."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "action": "turn_on",
                "params": {"brightness": 100}
            }
        ]
    }
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["device_id"] == "light_1"
    assert result["results"][0]["status"] == "success"


def test_process_multiple_actions(device_controller):
    """Test processing multiple device actions."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "action": "turn_on",
                "params": {"brightness": 100}
            },
            {
                "device_id": "thermostat_1",
                "action": "set_temperature",
                "params": {"temperature": 21}
            }
        ]
    }
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 2
    assert all(r["status"] == "success" for r in result["results"])


def test_process_no_actions(device_controller):
    """Test processing with no actions."""
    input_data = {"actions": []}
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert "error" in result
    assert result["error"] == "No actions provided"


def test_process_invalid_action(device_controller):
    """Test processing an invalid device action."""
    input_data = {
        "actions": [
            {
                "device_id": "invalid_device",
                "action": "turn_on",
                "params": {"brightness": 100}
            }
        ]
    }
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "error"
    assert "Device invalid_device not found" in result["results"][0]["error"]


def test_process_missing_action_params(device_controller):
    """Test processing an action with missing parameters."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "action": "turn_on"
            }
        ]
    }
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success"


def test_process_action_error(device_controller):
    """Test error handling in action processing."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "action": "invalid_action",
                "params": {"brightness": 100}
            }
        ]
    }
    
    result = device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "success" 