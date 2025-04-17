"""
AutoGenManager for HomeyMind.

This manager orchestrates the interaction between different agents in the HomeyMind system,
handling the flow of structured data between agents and coordinating their actions.
"""

import asyncio
from typing import Dict, Any, List
from autogen import AssistantAgent, UserProxyAgent
from .base_agent import BaseAgent
from .intent_parser import IntentParser
from .sensor_agent import SensorAgent
from .homey_assistant import HomeyAssistant
from .tts_agent import TTSAgent
from .device_controller import DeviceController
from homey.mqtt_client import HomeyMQTTClient

class AutoGenManager:
    """Manager class for coordinating all agents in the HomeyMind system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the manager and all agents.
        
        Args:
            config: Configuration dictionary containing settings for all components
        """
        # Initialize MQTT client
        self.mqtt_client = HomeyMQTTClient(config["mqtt_config"])
        self.mqtt_client.connect()

        # Initialize all agents
        self.intent_parser = IntentParser(config, self.mqtt_client)
        self.sensor_agent = SensorAgent(config, self.mqtt_client)
        self.homey_assistant = HomeyAssistant(config, self.mqtt_client)
        self.tts_agent = TTSAgent(config, self.mqtt_client, config["tts_config"])
        self.device_controller = DeviceController(config, self.mqtt_client)

    async def process_intent_streaming(self, text: str) -> Dict[str, Any]:
        """Process user input through the agent pipeline.
        
        Args:
            text: User input text to process
            
        Returns:
            Dictionary containing the complete processing results
        """
        try:
            # Step 1: Parse intent
            intent_result = await self.intent_parser.process({"message": text})
            if intent_result["status"] != "success":
                return intent_result

            # Step 2: Get sensor data if needed
            sensor_data = {}
            if intent_result["intent"]["type"] == "read_sensor":
                sensor_data = await self.sensor_agent.process(intent_result["intent"])

            # Step 3: Generate response and action plan
            assistant_result = await self.homey_assistant.process({
                "intent": intent_result["intent"],
                "sensor_data": sensor_data
            })
            if assistant_result["status"] != "success":
                return assistant_result

            # Step 4: Handle TTS
            if "response" in assistant_result:
                await self.tts_agent.process({
                    "text": assistant_result["response"]
                })

            # Step 5: Execute device actions
            if "actions" in assistant_result:
                action_result = await self.device_controller.process({
                    "actions": assistant_result["actions"],
                    "requires_confirmation": assistant_result.get("requires_confirmation", True)
                })
                if action_result["status"] != "success":
                    return action_result

            # Return complete result
            return {
                "status": "success",
                "data": {
                    "intent": intent_result["intent"],
                    "sensor_data": sensor_data,
                    "response": assistant_result["response"],
                    "actions": assistant_result["actions"]
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Failed to process intent: {str(e)}"
            }

    def _log_error(self, message: str):
        """Log error message."""
        print(f"ERROR: {message}")

    async def close(self):
        """Clean up resources."""
        await self.mqtt_client.disconnect()
