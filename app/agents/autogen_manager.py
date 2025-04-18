"""
AutoGenManager for HomeyMind.

This manager orchestrates the interaction between different agents in the HomeyMind system,
handling the flow of structured data between agents and coordinating their actions.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List
from autogen import AssistantAgent, UserProxyAgent
from .base_agent import BaseAgent
from .intent_parser import IntentParser
from .planner_agent import PlannerAgent
from .sensor_agent import SensorAgent
from .homey_assistant import HomeyAssistant
from .tts_agent import TTSAgent
from .device_controller import DeviceController
from homey.mqtt_client import HomeyMQTTClient
from app.core.config import LLMConfig

class AutoGenManager(BaseAgent):
    """Manager for coordinating multiple agents in the HomeyMind system."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the AutoGenManager."""
        super().__init__(config)
        self.mqtt_client = HomeyMQTTClient(config.mqtt_config)
        self.mqtt_client.connect()
        
        # Initialize agents
        self.intent_parser = IntentParser(config)
        self.planner = PlannerAgent(config)
        self.sensor_agent = SensorAgent(config, self.mqtt_client)
        self.homey_assistant = HomeyAssistant(config, self.mqtt_client)
        self.tts_agent = TTSAgent(config, self.mqtt_client)
        self.device_controller = DeviceController(config, self.mqtt_client)
    
    async def process_intent_streaming(self, text: str) -> Dict[str, Any]:
        """Process user intent and generate streaming response.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary containing processing results
        """
        try:
            # Parse intent
            intent_result = await self.intent_parser.process(text)
            if intent_result["status"] == "error":
                return {"status": "error", "error": "Failed to process intent"}
            
            # Get sensor data if needed
            if intent_result["intent"]["type"] == "read_sensor":
                sensor_result = await self.sensor_agent.process(intent_result["intent"])
                if sensor_result["status"] == "error":
                    return {"status": "error", "error": sensor_result["error"]}
                intent_result["sensor_data"] = sensor_result
            
            # Process with assistant
            assistant_result = await self.homey_assistant.process(intent_result)
            if assistant_result["status"] == "error":
                return {"status": "error", "error": assistant_result["error"]}
            
            # Execute device actions
            if "actions" in assistant_result and assistant_result["actions"]:
                device_result = await self.device_controller.process(assistant_result["actions"])
                if device_result["status"] == "error":
                    return {"status": "error", "error": "Device not responding"}
                
            # Convert to speech
            if "response" in assistant_result:
                tts_result = await self.tts_agent.process({
                    "text": assistant_result["response"],
                    "zone": intent_result.get("zone", "all")
                })
                if tts_result["status"] == "error":
                    return {"status": "error", "error": "TTS service unavailable"}
                
            return {
                "status": "success",
                "response": assistant_result.get("response", ""),
                "actions": assistant_result.get("actions", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self) -> None:
        """Close all resources."""
        await self.mqtt_client.disconnect()

    def _log_error(self, message: str):
        """Log error message."""
        print(f"ERROR: {message}")
