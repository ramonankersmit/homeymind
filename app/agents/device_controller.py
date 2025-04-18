"""
Device Controller agent for HomeyMind.

This agent is responsible for executing device actions and coordinating device control
based on structured action plans.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent
from app.core.config import LLMConfig, Device
from .tool_registry import register_tool, Tool
from .schemas import (
    DeviceActionInput, DeviceActionOutput,
    DimDeviceInput, DeviceStatusInput, DeviceStatusOutput
)


class DeviceController(BaseAgent):
    """Agent that executes device actions and coordinates device control."""

    def __init__(self, config: LLMConfig):
        """Initialize the device controller.
        
        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.devices: List[Device] = config.openai.devices
        
        # Register tools
        register_tool(Tool(
            name="turn_on_device",
            func=self._execute_action,
            input_model=DeviceActionInput,
            output_model=DeviceActionOutput,
            description="Turn on a device"
        ))
        
        register_tool(Tool(
            name="turn_off_device",
            func=self._execute_action,
            input_model=DeviceActionInput,
            output_model=DeviceActionOutput,
            description="Turn off a device"
        ))
        
        register_tool(Tool(
            name="dim_device",
            func=self._execute_action,
            input_model=DimDeviceInput,
            output_model=DeviceActionOutput,
            description="Dim a device to a specific brightness"
        ))
        
        register_tool(Tool(
            name="get_device_status",
            func=self.get_device_status,
            input_model=DeviceStatusInput,
            output_model=DeviceStatusOutput,
            description="Get the current status of a device"
        ))

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute device actions and coordinate control.
        
        Args:
            input_data: Dictionary containing:
                {
                    "actions": [
                        {
                            "device_id": "light_1",
                            "action": "turn_on",
                            "params": {"brightness": 100}
                        }
                    ]
                }
            
        Returns:
            Dictionary containing:
                {
                    "status": "success",
                    "results": [
                        {
                            "device_id": "light_1",
                            "status": "success",
                            "message": "Light turned on"
                        }
                    ]
                }
        """
        actions = input_data.get("actions", [])

        if not actions:
            return {
                "status": "error",
                "error": "No actions provided"
            }

        results = []
        for action in actions:
            try:
                # Execute the action
                result = self._execute_action(action)
                results.append(result)
            except Exception as e:
                results.append({
                    "device_id": action.get("device_id"),
                    "status": "error",
                    "error": str(e)
                })

        # Check overall status
        all_success = all(r.get("status") == "success" for r in results)
        
        return {
            "status": "success" if all_success else "error",
            "results": results
        }

    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single device action.
        
        Args:
            action: Dictionary containing device action details
            
        Returns:
            Dictionary containing execution result
        """
        device_id = action.get("device_id")
        action_name = action.get("action")
        params = action.get("params", {})

        if not all([device_id, action_name]):
            raise ValueError("Missing required action parameters")

        # Find device in configuration
        device = next(
            (d for d in self.devices if d.id == device_id),
            None
        )
        
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Execute the action
        result = self.execute_device_action(device_id, action_name, params)
        
        return {
            "device_id": device_id,
            "status": "success",
            "message": f"Successfully executed {action_name}"
        } 