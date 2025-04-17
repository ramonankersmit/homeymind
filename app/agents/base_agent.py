"""
Base agent class for HomeyMind.

This module provides the base class for all AutoGen agents in the system.
"""

from typing import Dict, Any, Optional, Callable
import autogen
from autogen import AssistantAgent, UserProxyAgent
import logging
from datetime import datetime
from homey.mqtt_client import HomeyMQTTClient

def create_user_proxy() -> UserProxyAgent:
    """Create a user proxy agent with Docker disabled."""
    return UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config={"use_docker": False}
    )


class BaseAgent:
    """Base class for all agents in the HomeyMind system."""
    
    def __init__(self, config: Dict[str, Any], mqtt_client=None):
        """Initialize the agent with configuration and MQTT client."""
        self.config = config
        self.mqtt_client = mqtt_client
        self._message_handler = None
        
        # Initialize the AutoGen agent
        self.agent = AssistantAgent(
            name=config.get("name", "agent"),
            system_message=config.get("system_message", "You are a helpful assistant."),
            llm_config=config.get("llm_config", {})
        )

    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Set the message handler for this agent."""
        self._message_handler = handler
    
    def _log_message(self, message: str, role: str = "assistant") -> None:
        """Log a message and send it to the message handler if set."""
        if self._message_handler:
            self._message_handler({
                "role": role,
                "message": message,
                "agent": self.__class__.__name__
            })
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results."""
        raise NotImplementedError("Subclasses must implement process()")
    
    async def close(self) -> None:
        """Clean up resources."""
        pass

    async def execute_device_action(self, device_id: str, capability: str, value: Any) -> Dict[str, Any]:
        """Execute an action on a device through MQTT.
        
        Args:
            device_id: ID of the device to control
            capability: Device capability to control
            value: Value to set
            
        Returns:
            Dictionary containing the execution results
        """
        try:
            await self.mqtt_client.publish(
                f"device/{device_id}/{capability}/set",
                {"value": value}
            )
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def get_device_status(self, device_id: str, capability: str) -> Any:
        """Get the current status of a device capability through MQTT.
        
        Args:
            device_id: ID of the device to query
            capability: Device capability to query
            
        Returns:
            Current status value or error dictionary
        """
        try:
            status = await self.mqtt_client.get_status(
                f"device/{device_id}/{capability}"
            )
            return status
        except Exception as e:
            return {"error": str(e)} 