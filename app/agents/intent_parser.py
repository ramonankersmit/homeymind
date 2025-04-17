"""
Intent Parser agent for HomeyMind.

This agent is responsible for parsing user input into structured intents with confidence scores.
"""

from typing import Dict, Any
from app.agents.base_agent import BaseAgent


class IntentParser(BaseAgent):
    """Agent that parses user input into structured intents with confidence scores."""

    def __init__(self, config: Dict[str, Any], mqtt_client):
        """Initialize the intent parser.
        
        Args:
            config: Configuration dictionary
            mqtt_client: MQTT client for device communication
        """
        super().__init__(config, mqtt_client)
        self.zones = ["woonkamer", "keuken", "slaapkamer", "badkamer"]

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse user input into a structured intent.
        
        Args:
            input_data: Dictionary containing the user message
            
        Returns:
            Dictionary containing the parsed intent with confidence score
        """
        message = input_data.get("message", "").lower().strip()
        
        if not message:
            return {
                "status": "error",
                "error": "Empty message"
            }

        # Check for light control
        if "licht" in message and ("aan" in message or "uit" in message):
            zone = self._extract_zone(message)
            value = "on" if "aan" in message else "off"
            return {
                "status": "success",
                "intent": {
                    "type": "control",
                    "device_type": "light",
                    "zone": zone,
                    "value": value,
                    "confidence": 0.95
                }
            }

        # Check for thermostat control
        if "temperatuur" in message and any(str(i) in message for i in range(0, 31)):
            zone = self._extract_zone(message)
            value = next((int(i) for i in message.split() if i.isdigit() and 0 <= int(i) <= 30), None)
            if value is not None:
                return {
                    "status": "success",
                    "intent": {
                        "type": "control",
                        "device_type": "thermostat",
                        "zone": zone,
                        "value": value,
                        "confidence": 0.9
                    }
                }

        # Check for sensor read
        if any(q in message for q in ["wat is", "hoe warm", "hoe koud"]):
            if "temperatuur" in message:
                zone = self._extract_zone(message)
                return {
                    "status": "success",
                    "intent": {
                        "type": "read_sensor",
                        "device_type": "temperature",
                        "zone": zone,
                        "value": None,
                        "confidence": 0.85
                    }
                }

        # Check for "all lights" command
        if "alle lichten" in message and ("aan" in message or "uit" in message):
            value = "on" if "aan" in message else "off"
            return {
                "status": "success",
                "intent": {
                    "type": "control",
                    "device_type": "light",
                    "zone": "all",
                    "value": value,
                    "confidence": 0.8
                }
            }

        # Unknown intent
        return {
            "status": "success",
            "intent": {
                "type": "unknown",
                "device_type": None,
                "zone": None,
                "value": None,
                "confidence": 0.1
            }
        }

    def _extract_zone(self, message: str) -> str:
        """Extract zone from message.
        
        Args:
            message: User input message
            
        Returns:
            Extracted zone or default zone
        """
        for zone in self.zones:
            if zone in message:
                return zone
        return "woonkamer"  # Default zone 