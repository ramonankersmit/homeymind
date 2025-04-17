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
from homey.mqtt import HomeyMQTTClient


class AutoGenManager:
    """Manager class for orchestrating agent interactions."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AutoGenManager with configuration.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing:
                - llm_config: LLM configuration
                - mqtt_config: MQTT configuration
                - device_config: Device configuration
                - tts_config: TTS configuration
        """
        self.config = config
        self.mqtt_client = HomeyMQTTClient(config.get("mqtt_config", {}))
        self.agents = {}
        self._initialize_agents()

    def _initialize_agents(self):
        """Initialize all agents with their respective configurations."""
        # Initialize MQTT client first
        self.mqtt_client.connect()
        
        # Initialize agents in the correct order
        self.agents["sensor"] = SensorAgent(
            self.config.get("llm_config", {}),
            self.mqtt_client
        )
        
        self.agents["intent_parser"] = IntentParser(
            self.config.get("llm_config", {})
        )
        
        self.agents["assistant"] = HomeyAssistant(
            self.config.get("llm_config", {})
        )
        
        self.agents["tts"] = TTSAgent(
            self.config.get("llm_config", {}),
            self.mqtt_client,
            self.config.get("tts_config", {})
        )
        
        self.agents["device_controller"] = DeviceController(
            self.config.get("llm_config", {}),
            self.mqtt_client
        )

    async def process_intent_streaming(self, message: str) -> Dict[str, Any]:
        """
        Process user intent with streaming response.
        
        Args:
            message (str): User's input message
            
        Returns:
            Dict[str, Any]: Processing result with status and data
                {
                    "status": "success",
                    "data": {
                        "intent": {...},
                        "sensor_data": {...},
                        "response": {...},
                        "actions": {...}
                    }
                }
        """
        result = {
            "status": "success",
            "data": {}
        }
        
        try:
            # Step 1: Parse intent
            intent_result = await self.agents["intent_parser"].process({
                "message": message
            })
            result["data"]["intent"] = intent_result
            
            # Step 2: Get sensor data if needed
            if intent_result.get("intent", {}).get("type") in ["read_sensor", "set_temperature"]:
                sensor_result = await self.agents["sensor"].process({
                    "intent": intent_result["intent"]
                })
                result["data"]["sensor_data"] = sensor_result
            
            # Step 3: Generate response and actions
            assistant_result = await self.agents["assistant"].process({
                "intent": intent_result["intent"],
                "confidence": intent_result["confidence"],
                "raw_input": message,
                "device_status": result["data"].get("sensor_data", {})
            })
            result["data"]["response"] = assistant_result
            
            # Step 4: Handle TTS if needed
            if assistant_result.get("response"):
                tts_result = await self.agents["tts"].process({
                    "text": assistant_result["response"]
                })
                result["data"]["tts"] = tts_result
            
            # Step 5: Execute device actions if needed
            if assistant_result.get("actions"):
                action_result = await self.agents["device_controller"].process({
                    "actions": assistant_result["actions"],
                    "requires_confirmation": assistant_result.get("requires_confirmation", True)
                })
                result["data"]["actions"] = action_result
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self._log_error(f"Error processing intent: {e}")
        
        return result

    def _log_error(self, message: str):
        """Log error message."""
        print(f"ERROR: {message}")

    async def close(self):
        """Close all connections and cleanup."""
        await self.mqtt_client.disconnect()
        for agent in self.agents.values():
            if hasattr(agent, "close"):
                await agent.close()
