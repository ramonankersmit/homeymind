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

class AutoGenManager: 
    """Manager for coordinating multiple agents in the HomeyMind system."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client=None):
        """Initialize the manager with configuration and MQTT client."""
        self.config = config
        self.mqtt_client = mqtt_client
        
        # Initialize all agents
        self.agents = {
            "parser": IntentParser(config, mqtt_client),
            "planner": PlannerAgent(config, mqtt_client),
            "sensor": SensorAgent(config, mqtt_client),
            "assistant": HomeyAssistant(config, mqtt_client),
            "tts": TTSAgent(config, mqtt_client),
            "device": DeviceController(config, mqtt_client)
        }
    
    async def process_intent_streaming(self, text: str):
        """Process user input through the agent pipeline."""
        # 0) Start
        yield {"role": "manager", "message": "Ik verwerk je bericht..."}
        
        try:
            # 1) Parse intent
            yield {"role": "intent_parser", "message": "Ik analyseer je verzoek om te begrijpen wat je wilt..."}
            intent_result = await self.agents["parser"].process({"message": text})
            if intent_result.get("status") != "success":
                yield {"role": "error", "message": intent_result}
                return
            
            # 2) Plan approach
            yield {"role": "planner", "message": "Ik plan de beste aanpak voor je verzoek..."}
            plan = await self.agents["planner"].process({"intent": intent_result["intent"]})
            if plan.get("status") != "success":
                yield {"role": "error", "message": plan}
                return
            
            # 3) Get sensor data if needed
            sensor_data = {}
            if intent_result["intent"].get("type") == "read_sensor":
                yield {"role": "sensor", "message": "Ik lees de sensorwaarden..."}
                sensor_data = await self.agents["sensor"].process({"intent": intent_result["intent"]})
                yield {"role": "sensor", "message": sensor_data}
            
            # 4) Generate response
            yield {"role": "assistant", "message": "Ik verwerk je bericht..."}
            assistant_result = await self.agents["assistant"].process({
                "intent": intent_result["intent"],
                "sensor_data": sensor_data,
                "plan": plan
            })
            yield {"role": "assistant", "message": assistant_result}
            if assistant_result.get("status") != "success":
                yield {"role": "error", "message": assistant_result}
                return
            
            # 5) Generate speech if needed
            if assistant_result.get("response"):
                yield {"role": "tts", "message": "Ik zet je bericht om naar spraak..."}
                tts_result = await self.agents["tts"].process({
                    "text": assistant_result["response"],
                    "zone": intent_result["intent"].get("zone", "woonkamer")
                })
                yield {"role": "tts", "message": tts_result}
            
            # 6) Execute device actions if needed
            if assistant_result.get("actions"):
                yield {"role": "device_controller", "message": "Ik voer de acties uit..."}
                action_result = await self.agents["device"].process({
                    "actions": assistant_result["actions"],
                    "requires_confirmation": assistant_result.get("needs_confirmation", False)
                })
                yield {"role": "device_controller", "message": action_result}
                if action_result.get("status") != "success":
                    yield {"role": "error", "message": action_result}
                    return
            
            # 7) Complete
            yield {"role": "manager", "message": "Verwerking voltooid"}
            
        except Exception as e:
            yield {"role": "error", "message": str(e)}
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.mqtt_client:
            await self.mqtt_client.disconnect()

    def _log_error(self, message: str):
        """Log error message."""
        print(f"ERROR: {message}")
