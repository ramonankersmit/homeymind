"""
HomeyAssistant agent for HomeyMind.

This agent is responsible for generating natural language responses and coordinating actions
based on parsed intents and device status.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class HomeyAssistant(BaseAgent):
    """Agent for coordinating actions and generating natural language responses."""

    def __init__(self, config: Dict[str, Any], mqtt_client=None):
        """Initialize the homey assistant."""
        super().__init__(config, mqtt_client)
        self.devices = config.get("devices", {})

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent and generate response with actions."""
        intent = input_data.get("intent", {})
        self._log_message(f"Processing intent: {intent}")
        
        intent_type = intent.get("type")
        zone = intent.get("zone")
        value = intent.get("value")
        
        if intent_type == "light_control":
            return await self._handle_light_control(zone, value)
        elif intent_type == "thermostat_control":
            return await self._handle_thermostat_control(zone, value)
        elif intent_type == "sensor_read":
            return await self._handle_sensor_read(zone)
        else:
            return self._create_error_response()

    async def _handle_light_control(self, zone: str, value: str) -> Dict[str, Any]:
        """Handle light control intent."""
        actions = []
        response = ""
        
        if zone == "all":
            for device_zone, devices in self.devices.items():
                for device in devices:
                    if device.get("type") == "light":
                        actions.append({
                            "device": device["id"],
                            "action": "set",
                            "value": value
                        })
            response = f"Turning {value} all lights"
        else:
            zone_devices = self.devices.get(zone, [])
            for device in zone_devices:
                if device.get("type") == "light":
                    actions.append({
                        "device": device["id"],
                        "action": "set",
                        "value": value
                    })
            response = f"Turning {value} lights in {zone}"
            
        self._log_message(f"Light control response: {response}")
        return {
            "response": response,
            "actions": actions,
            "needs_confirmation": self._needs_confirmation(actions)
        }

    async def _handle_thermostat_control(self, zone: str, value: float) -> Dict[str, Any]:
        """Handle thermostat control intent."""
        actions = []
        response = ""
        
        zone_devices = self.devices.get(zone, [])
        for device in zone_devices:
            if device.get("type") == "thermostat":
                actions.append({
                    "device": device["id"],
                    "action": "set",
                    "value": value
                })
                response = f"Setting temperature to {value}°C in {zone}"
                break
                
        if not response:
            response = f"No thermostat found in {zone}"
            
        self._log_message(f"Thermostat control response: {response}")
        return {
            "response": response,
            "actions": actions,
            "needs_confirmation": self._needs_confirmation(actions)
        }

    async def _handle_sensor_read(self, zone: str) -> Dict[str, Any]:
        """Handle sensor read intent."""
        response = f"Current sensor readings for {zone}:"
        zone_devices = self.devices.get(zone, [])
        
        for device in zone_devices:
            if device.get("type") in ["temperature_sensor", "humidity_sensor"]:
                status = await self.get_device_status(device["id"])
                if status:
                    response += f"\n- {device['type']}: {status.get('value', 'unknown')}"
                    
        self._log_message(f"Sensor read response: {response}")
        return {
            "response": response,
            "actions": [],
            "needs_confirmation": False
        }

    def _create_error_response(self) -> Dict[str, Any]:
        """Create error response for unknown intent."""
        response = "I'm sorry, I didn't understand that command."
        self._log_message(f"Error response: {response}")
        return {
            "response": response,
            "actions": [],
            "needs_confirmation": False
        }

    def _needs_confirmation(self, actions: List[Dict[str, Any]]) -> bool:
        """Determine if user confirmation is needed."""
        return len(actions) > 0 