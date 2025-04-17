"""
Base agent class for HomeyMind.

This module provides the base class for all AutoGen agents in the system.
"""

from typing import Dict, Any, Optional, Callable
import autogen
from autogen import AssistantAgent, UserProxyAgent
import logging
from datetime import datetime
from homey.mqtt_client import MQTTClient


def create_user_proxy() -> UserProxyAgent:
    """Create a user proxy agent with Docker disabled."""
    return UserProxyAgent(
        name="user_proxy",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config={"use_docker": False}
    )


class BaseAgent:
    """Base agent class providing common functionality for all agents.
    
    This class provides the foundation for all agents in the system, including:
    - Basic configuration handling
    - MQTT client management
    - Common device interaction methods
    """

    def __init__(self, config: dict, mqtt_client):
        """Initialize the base agent.
        
        Args:
            config: Configuration dictionary containing agent settings
            mqtt_client: MQTT client instance for device communication
        """
        self.config = config
        self.mqtt_client = mqtt_client

    async def get_device_status(self, device_id: str, capability: str) -> Dict[str, Any]:
        """Get the current status of a device capability.
        
        Args:
            device_id: ID of the device to check
            capability: Capability to get status for
            
        Returns:
            Dictionary containing the status value and any additional information
        """
        topic = f"{device_id}/{capability}"
        try:
            return await self.mqtt_client.get_status(topic)
        except Exception as e:
            return {"error": str(e)}

    async def execute_device_action(self, device_id: str, capability: str, value: Any) -> Dict[str, Any]:
        """Execute an action on a device capability.
        
        Args:
            device_id: ID of the device to control
            capability: Capability to modify
            value: New value to set
            
        Returns:
            Dictionary indicating success/failure and any error message
        """
        topic = f"{device_id}/{capability}/set"
        payload = {"value": value}
        try:
            await self.mqtt_client.publish(topic, payload)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results.
        
        This method must be implemented by subclasses to provide specific
        agent functionality.
        
        Args:
            input_data: Dictionary containing input data for processing
            
        Returns:
            Dictionary containing processing results
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement process()")

    def _create_agent(self) -> AssistantAgent:
        """
        Create the AutoGen agent instance with proper LLM configuration.
        
        This method sets up the agent with either local or cloud-based LLM configuration
        based on the provided settings.
        """
        # Get model settings
        model = self.config.get('model', 'gpt-4')
        
        # Create agent with specified LLM configuration
        return AssistantAgent(
            name=self.config.get('name', 'base_agent'),
            llm_config={
                "config_list": [{
                    "model": model,
                    "api_key": self.config.get('api_key'),
                    "base_url": self.config.get('base_url'),
                    "api_type": self.config.get('api_type', 'openai'),
                    "api_version": self.config.get('api_version'),
                }],
                "temperature": self.config.get('temperature', 0.7),
                **{k: v for k, v in self.config.items() if k not in ['config_list', 'temperature', 'model', 'api_key', 'base_url', 'api_type', 'api_version']}
            },
            system_message=self.config.get('system_message', "You are a helpful assistant.")
        )

    def set_message_handler(self, handler: Callable):
        """
        Set a handler for realtime message updates.
        
        Args:
            handler (Callable): Function to handle message updates
        """
        self.message_handler = handler
        
    def clear_message_handler(self):
        """Clear the message handler."""
        self.message_handler = None

    def log(self, message: str, level: str = "info"):
        """
        Log a message with timestamp.
        
        Args:
            message (str): Message to log
            level (str): Log level (info, warning, error)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {self.config.get('name', 'base_agent')}: {message}"
        
        if level == "error":
            logging.getLogger(f"agent.{self.config.get('name', 'base_agent')}").error(log_message)
        elif level == "warning":
            logging.getLogger(f"agent.{self.config.get('name', 'base_agent')}").warning(log_message)
        else:
            logging.getLogger(f"agent.{self.config.get('name', 'base_agent')}").info(log_message)

    def _log_message(self, message: str, role: str = "assistant"):
        """
        Log a message and notify handlers.
        
        Args:
            message (str): Message to log
            role (str): Role of the message sender
        """
        self.log(message)
        
        # Notify the message handler if set
        if self.message_handler:
            self.message_handler({
                "role": role,
                "message": message,
                "agent": self.config.get('name', 'base_agent'),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
        # Also notify the on_message callback if set
        if self.on_message:
            self.on_message(self.config.get('name', 'base_agent'), message, role) 