"""
IntentParser agent for HomeyMind.

This agent is responsible for parsing user input into structured intents.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class IntentParser(BaseAgent):
    """Agent responsible for parsing user intents."""

    async def process(self, input_data: str) -> Dict[str, Any]:
        """
        Parse user input into structured intent.
        
        Args:
            input_data (str): Raw user input to parse
            
        Returns:
            Dict[str, Any]: Parsed intent with confidence score
        """
        user_proxy = create_user_proxy()
        
        self._log_message(f"Parsing intent: {input_data}", "planner")

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=f"Parse this command into intent: {input_data}",
            clear_history=True
        )

        response = chat_result.summary
        self._log_message(response, "planner")

        return {
            'text': input_data,
            'intent': response,
            'confidence': 0.9  # Placeholder for later evaluation
        } 