from typing import Dict, Any, Optional
from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Generates action proposals based on intent and current status."""
    
    async def process(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate an action proposal based on intent and current status."""
        intent = input_data.get("intent")
        status = input_data.get("status")
        
        if not intent or not status:
            self.log("Missing intent or status data")
            return None
        
        # Example: Temperature control
        if intent.get("type") == "temperature":
            current_temp = status.get("temperature", 0)
            desired_temp = 20  # Default comfort temperature
            
            if current_temp < desired_temp:
                return {
                    "action": "set_temperature",
                    "device": "thermostat",
                    "value": desired_temp,
                    "reason": f"Temperature is {current_temp}°C, setting to {desired_temp}°C"
                }
        
        # Example: Light control
        elif intent.get("type") == "light":
            current_state = status.get("state", "off")
            desired_state = "on" if intent.get("action") == "turn_on" else "off"
            
            if current_state != desired_state:
                return {
                    "action": f"turn_{desired_state}",
                    "device": intent.get("device"),
                    "reason": f"Light is currently {current_state}, turning {desired_state}"
                }
        
        self.log(f"No action needed for intent: {intent}")
        return None 