"""
HomeyAssistant agent for HomeyMind.

This agent serves as the main assistant, processing user requests and coordinating responses.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class HomeyAssistant(BaseAgent):
    """Main assistant agent for HomeyMind."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and validate intents, provide responses.
        
        Args:
            input_data (Dict[str, Any]): Input data containing the user's message
            
        Returns:
            Dict[str, Any]: Processed result with response and action flag
        """
        user_proxy = create_user_proxy()
        
        message = input_data.get('text', '')
        self._log_message(f"Processing request: {message}", "user")

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=message,
            clear_history=True
        )

        response = chat_result.summary
        self._log_message(response, "assistant")

        return {
            'response': response,
            'requires_device_action': 'device_action' in response.lower()
        } 