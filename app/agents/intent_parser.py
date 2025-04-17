"""
Intent Parser agent for HomeyMind.

This agent is responsible for parsing user input into structured intents with confidence scores.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class IntentParser(BaseAgent):
    """Agent responsible for parsing user input into structured intents."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse user input into a structured intent with confidence score.
        
        Args:
            input_data (Dict[str, Any]): Input containing user message
                {
                    "message": "Zet de lampen in de woonkamer op 80%"
                }
            
        Returns:
            Dict[str, Any]: Parsed intent with confidence score
                {
                    "intent": {
                        "type": "set_brightness",
                        "device_type": "light",
                        "zone": "woonkamer",
                        "value": 80
                    },
                    "confidence": 0.95,
                    "raw_input": "Zet de lampen in de woonkamer op 80%"
                }
        """
        user_proxy = create_user_proxy()
        
        self._log_message("Parsing intent...", "intent_parser")

        # Create prompt for structured output
        prompt = f"""Parse the following user input into a structured intent.

Input: {input_data.get('message', '')}

Respond with a JSON object in this format:
{{
    "intent": {{
        "type": "intent_type",
        "device_type": "device_type",
        "zone": "zone_name",
        "value": value
    }},
    "confidence": confidence_score,
    "raw_input": "original_input"
}}

The intent type should be one of:
- set_brightness
- set_temperature
- turn_on
- turn_off
- read_sensor
- other

The device type should be one of:
- light
- thermostat
- sensor
- other

The zone should be a specific room or area name.
The value should be a number for numeric actions, or null for non-numeric actions.
The confidence score should be between 0 and 1."""

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
                self._log_message(f"Parsed intent: {result}", "intent_parser")
                return result
        except Exception as e:
            self.log(f"Failed to parse intent: {e}", level="error")

        # Fallback to basic response
        return {
            "intent": {
                "type": "other",
                "device_type": "other",
                "zone": None,
                "value": None
            },
            "confidence": 0.0,
            "raw_input": input_data.get('message', '')
        } 