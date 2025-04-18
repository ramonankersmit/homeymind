"""
AutoGenManager for HomeyMind.

This manager orchestrates the interaction between different agents in the HomeyMind system,
handling the flow of structured data between agents and coordinating their actions.
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, Any, List
from autogen import AssistantAgent, UserProxyAgent
from .base_agent import BaseAgent
from .intent_parser import IntentParser
from .planner_agent import PlannerAgent
from .sensor_agent import SensorAgent
from .homey_assistant import HomeyAssistant
from .tts_agent import TTSAgent
from .device_controller import DeviceController
from .tool_registry import get_all_tools
from homey.mqtt_client import HomeyMQTTClient
from app.core.config import LLMConfig
from app.core.observability import (
    get_logger, ToolMetrics, SessionMetrics,
    log_tool_call, log_tool_result, log_error
)

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
        
        # Get all registered tools
        self.tools = get_all_tools()
        
        # Generate function definitions for OpenAI
        self.functions = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_model.schema()
            }
            for tool in self.tools.values()
        ]
        
        # Initialize logger
        self.logger = get_logger("autogen_manager")
    
    async def process_intent_streaming(self, text: str, session_id: str = None) -> Dict[str, Any]:
        """Process user intent and generate streaming response."""
        try:
            with SessionMetrics(session_id or "default"):
                # Parse intent
                intent_result = await self.intent_parser.process(text)
                if intent_result["status"] == "error":
                    return {"status": "error", "error": "Failed to process intent"}
                
                # Initialize context
                context = [{"role": "user", "content": text}]
                plan = []
                
                while True:
                    # Get response from OpenAI with function calling
                    response = await self._call_openai(context)
                    msg = response.choices[0].message
                    
                    if msg.get("function_call"):
                        # Execute function call
                        name = msg.function_call.name
                        args = json.loads(msg.function_call.arguments)
                        
                        # Get and validate tool
                        tool = self.tools[name]
                        validated_args = tool.validate_input(args)
                        
                        # Log tool call
                        log_tool_call(self.logger, name, validated_args.dict())
                        
                        try:
                            with ToolMetrics(name):
                                # Execute tool
                                output = await tool.func(validated_args.dict())
                                validated_output = tool.validate_output(output)
                                
                                # Log tool result
                                log_tool_result(self.logger, name, validated_output.dict())
                                
                                # Add to context
                                context.append({
                                    "role": "function",
                                    "name": name,
                                    "content": json.dumps(validated_output.dict())
                                })
                                
                                # Add to plan
                                plan.append((name, args))
                        except Exception as e:
                            log_error(self.logger, e, {"tool": name, "args": args})
                            raise
                    else:
                        # Final response
                        return {
                            "status": "success",
                            "plan": plan,
                            "response": msg.content
                        }
            
        except Exception as e:
            log_error(self.logger, e, {"text": text, "session_id": session_id})
            return {"status": "error", "error": str(e)}
    
    async def _call_openai(self, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call OpenAI API with function calling enabled."""
        return await self.agent.generate_reply(
            messages=context,
            functions=self.functions,
            function_call="auto"
        )

    async def close(self) -> None:
        """Close all resources."""
        await self.mqtt_client.disconnect()

    def _log_error(self, message: str):
        """Log error message."""
        print(f"ERROR: {message}")
