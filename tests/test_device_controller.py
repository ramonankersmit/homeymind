"""Tests for the DeviceController class."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.agents.device_controller import DeviceController


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
    client.execute_action = Mock(return_value=True)
    client.get_status = Mock(return_value={"value": "on"})
    return client


@pytest.fixture
def device_controller(mock_config, mock_mqtt_client):
    """Create a DeviceController instance with mocked dependencies."""
    return DeviceController(mock_config, mock_mqtt_client)


@pytest.mark.asyncio
async def test_process_single_action(device_controller, mock_mqtt_client):
    """Test processing a single device action."""
    result = await device_controller.process({
        "actions": [{
            "device_id": "woonkamer_light",
            "capability": "onoff",
            "value": "on"
        }],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["device_id"] == "woonkamer_light"
    assert result["results"][0]["success"] is True
    assert result["results"][0]["error"] is None
    
    mock_mqtt_client.execute_action.assert_called_once_with(
        "woonkamer_light",
        "onoff",
        "on"
    )


@pytest.mark.asyncio
async def test_process_multiple_actions(device_controller, mock_mqtt_client):
    """Test processing multiple device actions."""
    result = await device_controller.process({
        "actions": [
            {
                "device_id": "woonkamer_light",
                "capability": "onoff",
                "value": "on"
            },
            {
                "device_id": "keuken_light",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 2
    assert all(r["success"] is True for r in result["results"])
    assert mock_mqtt_client.execute_action.call_count == 2


@pytest.mark.asyncio
async def test_process_action_with_status_check(device_controller, mock_mqtt_client):
    """Test processing action with status verification."""
    result = await device_controller.process({
        "actions": [{
            "device_id": "woonkamer_light",
            "capability": "onoff",
            "value": "on",
            "verify_status": True
        }],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is True
    assert result["results"][0]["status"] == "on"
    
    mock_mqtt_client.execute_action.assert_called_once()
    mock_mqtt_client.get_status.assert_called_once_with(
        "woonkamer_light",
        "onoff"
    )


@pytest.mark.asyncio
async def test_process_action_error(device_controller, mock_mqtt_client):
    """Test handling action execution error."""
    mock_mqtt_client.execute_action.side_effect = Exception("Action failed")
    
    result = await device_controller.process({
        "actions": [{
            "device_id": "woonkamer_light",
            "capability": "onoff",
            "value": "on"
        }],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is False
    assert "Action failed" in result["results"][0]["error"]


@pytest.mark.asyncio
async def test_process_status_check_error(device_controller, mock_mqtt_client):
    """Test handling status check error."""
    mock_mqtt_client.get_status.side_effect = Exception("Status check failed")
    
    result = await device_controller.process({
        "actions": [{
            "device_id": "woonkamer_light",
            "capability": "onoff",
            "value": "on",
            "verify_status": True
        }],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 1
    assert result["results"][0]["success"] is True
    assert result["results"][0]["status"] is None
    assert "Status check failed" in result["results"][0]["error"]


@pytest.mark.asyncio
async def test_process_empty_actions(device_controller):
    """Test processing with no actions."""
    result = await device_controller.process({
        "actions": [],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 0


@pytest.mark.asyncio
async def test_process_invalid_action(device_controller):
    """Test processing invalid action format."""
    result = await device_controller.process({
        "actions": [{
            "device_id": "woonkamer_light"
            # Missing required fields
        }],
        "requires_confirmation": False
    })
    
    assert result["status"] == "error"
    assert "Invalid action format" in result["error"]


@pytest.mark.asyncio
async def test_process_mixed_success(device_controller, mock_mqtt_client):
    """Test processing with mixed success/failure results."""
    mock_mqtt_client.execute_action.side_effect = [
        True,  # First action succeeds
        Exception("Second action failed")  # Second action fails
    ]
    
    result = await device_controller.process({
        "actions": [
            {
                "device_id": "woonkamer_light",
                "capability": "onoff",
                "value": "on"
            },
            {
                "device_id": "keuken_light",
                "capability": "onoff",
                "value": "on"
            }
        ],
        "requires_confirmation": False
    })
    
    assert result["status"] == "success"
    assert len(result["results"]) == 2
    assert result["results"][0]["success"] is True
    assert result["results"][1]["success"] is False
    assert "Second action failed" in result["results"][1]["error"] 