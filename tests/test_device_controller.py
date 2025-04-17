"""Tests for the DeviceController agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.agents.device_controller import DeviceController


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return {
        "devices": [
            {
                "id": "light_1",
                "type": "light",
                "zone": "woonkamer"
            },
            {
                "id": "thermostat_1",
                "type": "thermostat",
                "zone": "woonkamer"
            }
        ]
    }


@pytest.fixture
def mock_mqtt_client():
    """Create a mock MQTT client."""
    return AsyncMock()


@pytest.fixture
def device_controller(mock_config, mock_mqtt_client):
    """Create a DeviceController instance with mock dependencies."""
    return DeviceController(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_process_single_action(device_controller):
    """Test processing a single device action."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["device_id"] == "light_1"
    assert result["results"][0]["status"] == "success"
    assert "Successfully executed" in result["results"][0]["message"]


@pytest.mark.asyncio
async def test_process_multiple_actions(device_controller):
    """Test processing multiple device actions."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff",
                "value": "on"
            },
            {
                "device_id": "thermostat_1",
                "capability": "target_temperature",
                "value": 21
            }
        ],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "success"
    assert len(result["results"]) == 2
    assert all(r["status"] == "success" for r in result["results"])


@pytest.mark.asyncio
async def test_process_no_actions(device_controller):
    """Test processing with no actions provided."""
    input_data = {
        "actions": [],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert "No actions provided" in result["error"]


@pytest.mark.asyncio
async def test_process_invalid_action(device_controller):
    """Test processing an invalid device action."""
    input_data = {
        "actions": [
            {
                "device_id": "unknown_device",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "error"
    assert "Device unknown_device not found" in result["results"][0]["error"]


@pytest.mark.asyncio
async def test_process_missing_action_params(device_controller):
    """Test processing an action with missing parameters."""
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff"
                # Missing value parameter
            }
        ],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "error"
    assert "Missing required action parameters" in result["results"][0]["error"]


@pytest.mark.asyncio
async def test_process_action_error(device_controller):
    """Test handling of action execution error."""
    # Configure mock to raise an exception
    device_controller.execute_device_action = AsyncMock(side_effect=Exception("Action failed"))
    
    input_data = {
        "actions": [
            {
                "device_id": "light_1",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    }
    
    result = await device_controller.process(input_data)
    
    assert result["status"] == "error"
    assert len(result["results"]) == 1
    assert result["results"][0]["status"] == "error"
    assert "Action failed" in result["results"][0]["error"] 