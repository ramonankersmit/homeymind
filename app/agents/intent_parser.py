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

        # Get available devices if MQTT client is present
        devices = []
        if self.mqtt_client:
            try:
                devices = await self.mqtt_client.get_devices()
                self._log_message(f"Found {len(devices)} devices")
            except Exception as e:
                self.log(f"Could not fetch devices: {e}", level="warning")

        # Create prompt for structured output
        prompt = f"""Parse the following Dutch command into a structured intent.
Available devices: {[d.get('name', 'Unknown') for d in devices]}

Command: {input_data}

Respond with a JSON object in this format:
{{
    "text": "original command",
    "intent": "intent_type",
    "confidence": 0.0 to 1.0,
    "entities": {{
        "device": "matched_device_name",
        "action": "action_type",
        "parameters": {{
            "param1": "value1"
        }}
    }}
}}"""

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=prompt,
            clear_history=True
        )

        # Parse the response to extract JSON
        try:
            import json
            response = chat_result.summary
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                self._log_message(f"Parsed intent: {result}", "planner")
                return result
        except Exception as e:
            self.log(f"Failed to parse intent: {e}", level="error")

        # Fallback to basic response
        return {
            'text': input_data,
            'intent': 'unknown',
            'confidence': 0.0,
            'entities': {}
        } 