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
        self._log_message(f"Executing command: {command}", "executor")

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=f"Execute device control: {command}",
            clear_history=True
        )

        response = chat_result.summary
        self._log_message(response, "executor")

        return {
            'action': response,
            'status': 'success' if 'success' in response.lower() else 'failed'
        } 