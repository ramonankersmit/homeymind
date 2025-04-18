"""
HomeyAssistant agent for HomeyMind.

This agent is responsible for generating natural language responses and coordinating actions
based on parsed intents and device status.
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent
import logging
from app.core.config import LLMConfig
from app.agents.sensor_agent import SensorAgent

logger = logging.getLogger(__name__)

class HomeyAssistant(BaseAgent):
    """Agent for coordinating actions and generating natural language responses."""

    def __init__(self, config: LLMConfig, mqtt_client=None):
        """Initialize the homey assistant."""
        super().__init__(config)
        self.mqtt_client = mqtt_client
        self.devices = getattr(config, "devices", {})
        self.sensor_agent = SensorAgent(config, mqtt_client)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent and generate response with actions."""
        intent = input_data.get("intent", {})
        self._log_message("info", f"Processing intent: {intent}")
        
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
                            "device": device["id"].replace("_", ""),
                            "action": "set",
                            "value": value
                        })
            response = f"Turning {value} all lights"
        else:
            zone_devices = self.devices.get(zone, [])
            for device in zone_devices:
                if device.get("type") == "light":
                    actions.append({
                        "device": device["id"].replace("_", ""),
                        "action": "set",
                        "value": value
                    })
            response = f"Turning {value} lights in {zone}"
            
        self._log_message("info", f"Light control response: {response}")
        return {
            "status": "success",
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
                    "device": device["id"].replace("_", ""),
                    "action": "set",
                    "value": value
                })
                response = f"Setting temperature to {value}°C in {zone}"
                break
                
        if not response:
            response = f"No thermostat found in {zone}"
            
        self._log_message("info", f"Thermostat control response: {response}")
        return {
            "status": "success",
            "response": response,
            "actions": actions,
            "needs_confirmation": self._needs_confirmation(actions)
        }

    async def _handle_sensor_read(self, zone: str) -> Dict[str, Any]:
        """Handle sensor read intent."""
        try:
            # Get sensor data from sensor agent
            sensor_data = await self.sensor_agent.process_sensor_data(zone)
            if sensor_data["status"] == "error":
                return {
                    "status": "error",
                    "message": sensor_data["message"],
                    "response": "Failed to read sensor data",
                    "actions": [],
                    "needs_confirmation": False
                }
            
            return {
                "status": "success",
                "message": "Sensor data retrieved successfully",
                "response": sensor_data["response"],
                "actions": [],
                "needs_confirmation": False
            }
        except Exception as e:
            logger.error(f"Error handling sensor read: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to read sensor data",
                "response": "Failed to read sensor data",
                "actions": [],
                "needs_confirmation": False
            }

    def _create_error_response(self) -> Dict[str, Any]:
        """Create error response for unknown intent."""
        response = "I'm sorry, I didn't understand that command."
        self._log_message("error", f"Error response: {response}")
        return {
            "response": response,
            "actions": [],
            "needs_confirmation": False
        }

    def _needs_confirmation(self, actions: List[Dict[str, Any]]) -> bool:
        """Determine if user confirmation is needed."""
        return len(actions) > 0 

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent and return response."""
        try:
            intent_type = intent.get("type")
            if not intent_type:
                return {
                    "status": "error",
                    "message": "No intent type specified",
                    "response": "I'm sorry, I couldn't understand what you want me to do.",
                    "actions": []
                }

            handler = self.intent_handlers.get(intent_type)
            if not handler:
                return {
                    "status": "error",
                    "message": f"Unknown intent type: {intent_type}",
                    "response": "I'm sorry, I don't know how to handle that request.",
                    "actions": []
                }

            return await handler(intent)
        except Exception as e:
            self._log_message("error", f"Error processing intent: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "response": "I'm sorry, something went wrong while processing your request.",
                "actions": []
            } 