"""
Device Controller agent for HomeyMind.

This agent is responsible for executing device actions and coordinating device control
based on structured action plans.
"""

from typing import Dict, Any, List
from app.agents.base_agent import BaseAgent


class DeviceController(BaseAgent):
    """Agent that executes device actions and coordinates device control."""

    def __init__(self, config: Dict[str, Any], mqtt_client):
        """Initialize the device controller.
        
        Args:
            config: Configuration dictionary
            mqtt_client: MQTT client for device communication
        """
        super().__init__(config, mqtt_client)
        self.devices = config.get("devices", [])

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute device actions and coordinate control.
        
        Args:
            input_data: Dictionary containing:
                {
                    "actions": [
                        {
                            "device_id": "light_1",
                            "capability": "onoff",
                            "value": "on"
                        }
                    ],
                    "requires_confirmation": true
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
        requires_confirmation = input_data.get("requires_confirmation", True)

        if not actions:
            return {
                "status": "error",
                "error": "No actions provided"
            }

        results = []
        for action in actions:
            try:
                # Execute the action
                result = await self._execute_action(action)
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

    async def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single device action.
        
        Args:
            action: Dictionary containing device action details
            
        Returns:
            Dictionary containing execution result
        """
        device_id = action.get("device_id")
        capability = action.get("capability")
        value = action.get("value")

        if not all([device_id, capability, value]):
            raise ValueError("Missing required action parameters")

        # Find device in configuration
        device = next(
            (d for d in self.devices if d.get("id") == device_id),
            None
        )
        
        if not device:
            raise ValueError(f"Device {device_id} not found")

        # Execute the action
        await self.execute_device_action(device_id, capability, value)
        
        return {
            "device_id": device_id,
            "status": "success",
            "message": f"Successfully executed {capability} = {value}"
        } 