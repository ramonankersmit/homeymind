"""
HomeyAssistant agent for HomeyMind.

This agent is responsible for generating natural language responses and coordinating actions
based on parsed intents and device status.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class HomeyAssistant(BaseAgent):
    """Agent responsible for generating natural language responses and coordinating actions."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate natural language response and coordinate actions based on intent.
        
        Args:
            input_data (Dict[str, Any]): Input containing parsed intent and device status
                {
                    "intent": {
                        "type": "set_brightness",
                        "device_type": "light",
                        "zone": "woonkamer",
                        "value": 80
                    },
                    "confidence": 0.95,
                    "raw_input": "Zet de lampen in de woonkamer op 80%",
                    "device_status": {
                        "woonkamer_lamp": {
                            "on": true,
                            "brightness": 50
                        }
                    }
                }
            
        Returns:
            Dict[str, Any]: Response with natural language and action coordination
                {
                    "response": "Ik zal de lampen in de woonkamer op 80% zetten.",
                    "actions": [
                        {
                            "device_id": "woonkamer_lamp",
                            "capability": "brightness",
                            "value": 80
                        }
                    ],
                    "requires_confirmation": false
                }
        """
        user_proxy = create_user_proxy()
        
        self._log_message("Generating response...", "homey_assistant")

        # Create prompt for response generation
        prompt = f"""Generate a natural language response and coordinate actions based on the following intent and device status.

Intent: {input_data.get('intent', {})}
Device Status: {input_data.get('device_status', {})}

Respond with a JSON object in this format:
{{
    "response": "natural_language_response",
    "actions": [
        {{
            "device_id": "device_id",
            "capability": "capability_name",
            "value": value
        }}
    ],
    "requires_confirmation": true/false
}}

The response should be:
1. Natural and conversational
2. Acknowledge the user's request
3. State what will be done
4. Include any relevant device status information

The actions should be:
1. Specific to the devices that need to be controlled
2. Include the exact capability and value to set
3. Only include actions that are necessary

Set requires_confirmation to true if:
1. The action is potentially dangerous (e.g., turning off all lights)
2. The confidence score is below 0.8
3. Multiple devices are affected
4. The current state differs significantly from the requested state"""

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
                self._log_message(f"Generated response: {result}", "homey_assistant")
                return result
        except Exception as e:
            self.log(f"Failed to generate response: {e}", level="error")

        # Fallback to basic response
        return {
            "response": "Ik heb je verzoek ontvangen, maar kon geen specifieke actie bepalen.",
            "actions": [],
            "requires_confirmation": True
        } 