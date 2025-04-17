"""
Device Controller agent for HomeyMind.

This agent is responsible for executing device actions and coordinating device control
based on structured action plans.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class DeviceController(BaseAgent):
    """Agent responsible for executing device actions and coordinating device control."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute device actions and coordinate device control.
        
        Args:
            input_data (Dict[str, Any]): Input containing actions to execute
                {
                    "actions": [
                        {
                            "device_id": "woonkamer_lamp",
                            "capability": "brightness",
                            "value": 80
                        }
                    ],
                    "requires_confirmation": false
                }
            
        Returns:
            Dict[str, Any]: Result of device actions
                {
                    "status": "success",
                    "executed_actions": [
                        {
                            "device_id": "woonkamer_lamp",
                            "capability": "brightness",
                            "value": 80,
                            "status": "success"
                        }
                    ],
                    "failed_actions": []
                }
        """
        self._log_message("Executing device actions...", "device_controller")
        
        actions = input_data.get("actions", [])
        requires_confirmation = input_data.get("requires_confirmation", True)
        
        if requires_confirmation:
            return {
                "status": "pending_confirmation",
                "message": "Bevestig alstublieft de volgende acties:",
                "actions": actions
            }
        
        executed_actions = []
        failed_actions = []
        
        for action in actions:
            try:
                device_id = action["device_id"]
                capability = action["capability"]
                value = action["value"]
                
                # Execute the device action
                result = await self.execute_device_action(
                    device_id=device_id,
                    capability=capability,
                    value=value
                )
                
                if result.get("success", False):
                    executed_actions.append({
                        "device_id": device_id,
                        "capability": capability,
                        "value": value,
                        "status": "success"
                    })
                else:
                    failed_actions.append({
                        "device_id": device_id,
                        "capability": capability,
                        "value": value,
                        "status": "failed",
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                failed_actions.append({
                    "device_id": action.get("device_id", "unknown"),
                    "capability": action.get("capability", "unknown"),
                    "value": action.get("value", None),
                    "status": "failed",
                    "error": str(e)
                })
        
        # Determine overall status
        if failed_actions and executed_actions:
            status = "partial_success"
        elif failed_actions:
            status = "failed"
        else:
            status = "success"
        
        return {
            "status": status,
            "executed_actions": executed_actions,
            "failed_actions": failed_actions
        } 