"""
Planner agent for HomeyMind.

This agent is responsible for generating concrete action plans based on parsed intents
and available devices. It converts high-level intents into specific device actions.
"""

from typing import Dict, Any
from .base_agent import BaseAgent, create_user_proxy


class Planner(BaseAgent):
    """Agent responsible for planning device actions."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a concrete action plan from parsed intent and device list.
        
        Args:
            input_data (Dict[str, Any]): Input containing parsed intent and device list
                {
                    "intent": {
                        "type": "set_brightness",
                        "device_type": "light",
                        "zone": "woonkamer",
                        "value": 80
                    },
                    "devices": [
                        {
                            "id": "light1",
                            "name": "Lamp 1",
                            "type": "light",
                            "zone": "woonkamer",
                            "capabilities": ["onoff", "dim"]
                        }
                    ]
                }
            
        Returns:
            Dict[str, Any]: Action plan with specific device actions
                {
                    "actions": [
                        {
                            "device_id": "light1",
                            "action": "set_brightness",
                            "value": 80
                        }
                    ],
                    "requires_confirmation": true,
                    "confirmation_text": "Zal ik de lampen in de woonkamer op 80% zetten?"
                }
        """
        user_proxy = create_user_proxy()
        
        self._log_message("Planning actions...", "planner")

        # Create prompt for structured output
        prompt = f"""Given the following intent and available devices, create a concrete action plan.

Intent: {input_data.get('intent', {})}
Available devices: {input_data.get('devices', [])}

Respond with a JSON object in this format:
{{
    "actions": [
        {{
            "device_id": "device_id",
            "action": "action_type",
            "value": value
        }}
    ],
    "requires_confirmation": boolean,
    "confirmation_text": "Natural language confirmation prompt"
}}

The actions should be specific device commands that can be executed directly.
The confirmation_text should be a natural language question asking for user confirmation."""

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
                self._log_message(f"Generated plan: {result}", "planner")
                return result
        except Exception as e:
            self.log(f"Failed to generate plan: {e}", level="error")

        # Fallback to basic response
        return {
            "actions": [],
            "requires_confirmation": True,
            "confirmation_text": "Ik begrijp je verzoek, maar kan er geen concrete acties uit afleiden."
        } 