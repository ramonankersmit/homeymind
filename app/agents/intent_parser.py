"""
Intent Parser agent for HomeyMind.

This agent is responsible for parsing user input into structured intents with confidence scores.
"""

from typing import Dict, Any, Optional, List
from app.agents.base_agent import BaseAgent
from app.core.config import LLMConfig


class IntentParser(BaseAgent):
    """Agent for parsing user input into structured intents."""

    def __init__(self, config: LLMConfig):
        """Initialize the intent parser.
        
        Args:
            config: LLM configuration
        """
        super().__init__(config)
        self.zones: List[str] = getattr(config.openai, "zones", [])

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input and return structured intent."""
        message = input_data.get("message", "").lower()
        self._log_message("incoming", f"Processing message: {message}")
        
        # Extract zone from message
        zone = self._extract_zone(message)
        self._log_message("processing", f"Extracted zone: {zone}")
        
        # Determine intent type and confidence
        if "light" in message or "lamp" in message:
            if "all" in message:
                intent = {
                    "type": "light_control",
                    "zone": "all",
                    "value": "on" if "on" in message else "off",
                    "confidence": 0.9
                }
            else:
                intent = {
                    "type": "light_control",
                    "zone": zone,
                    "value": "on" if "on" in message else "off",
                    "confidence": 0.8
                }
        elif "temperature" in message or "thermostat" in message:
            intent = {
                "type": "thermostat_control",
                "zone": zone,
                "value": self._extract_temperature(message),
                "confidence": 0.8
            }
        elif "sensor" in message or "reading" in message:
            intent = {
                "type": "sensor_read",
                "zone": zone,
                "confidence": 0.7
            }
        else:
            intent = {
                "type": "unknown",
                "zone": zone,
                "confidence": 0.3
            }
            
        self._log_message("outgoing", f"Parsed intent: {intent}")
        return {"intent": intent}

    def _extract_zone(self, message: str) -> str:
        """Extract zone from message.
        
        Args:
            message: User input message
            
        Returns:
            Extracted zone or default zone
        """
        for zone in self.zones:
            if zone.lower() in message:
                return zone
        return "woonkamer"  # Default zone

    def _extract_temperature(self, message: str) -> Optional[float]:
        """Extract temperature value from message."""
        try:
            # Look for numbers in the message
            import re
            numbers = re.findall(r'\d+', message)
            if numbers:
                return float(numbers[0])
        except:
            pass
        return None 