"""
DeviceController agent for HomeyMind.

This agent is responsible for executing device control commands through Homey.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class DeviceController(BaseAgent):
    """Agent responsible for controlling home devices."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute device control commands.
        
        Args:
            input_data (Dict[str, Any]): Input data containing the command to execute
            
        Returns:
            Dict[str, Any]: Execution result with action and status
        """
        user_proxy = create_user_proxy()
        
        command = input_data.get('command', '')
        action = input_data.get('action', {})
        self._log_message(f"Executing command: {command}", "executor")

        # First let the LLM validate and refine the action
        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=f"Validate and refine device control action: {action}",
            clear_history=True
        )

        # Extract the refined action from the LLM response
        refined_action = action  # Default to original action
        try:
            import json
            start = chat_result.summary.find("{")
            end = chat_result.summary.rfind("}") + 1
            if start >= 0 and end > start:
                refined_action = json.loads(chat_result.summary[start:end])
        except Exception as e:
            self.log(f"Could not parse refined action: {e}", level="warning")

        # Execute the action through MQTT
        if self.mqtt_client:
            try:
                result = await self.execute_device_action(refined_action)
                self._log_message(f"MQTT execution result: {result}", "executor")
                return result
            except Exception as e:
                error_msg = f"MQTT execution failed: {str(e)}"
                self.log(error_msg, level="error")
                return {
                    'status': 'error',
                    'message': error_msg
                }
        else:
            self.log("No MQTT client available", level="error")
            return {
                'status': 'error',
                'message': 'No MQTT client available'
            } 