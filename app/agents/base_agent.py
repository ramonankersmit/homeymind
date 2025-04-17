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
    """Base class for all AutoGen agents in HomeyMind."""

    def __init__(
        self, 
        name: str, 
        llm_config: Dict[str, Any], 
        system_message: str,
        config: Dict[str, Any] = None,
        mqtt_client: Optional[MQTTClient] = None,
        on_message: Optional[Callable] = None
    ):
        """
        Initialize a base agent.

        Args:
            name (str): Name of the agent
            llm_config (Dict[str, Any]): LLM configuration
            system_message (str): System message defining the agent's role
            config (Dict[str, Any], optional): Agent-specific configuration
            mqtt_client (Optional[MQTTClient]): MQTT client for device communication
            on_message (Optional[Callable]): Callback for logging messages
        """
        self.name = name
        self.llm_config = llm_config
        self.system_message = system_message
        self.config = config or {}
        self.mqtt_client = mqtt_client
        self.on_message = on_message
        self.message_handler = None
        self.agent = self._create_agent()
        self.logger = logging.getLogger(f"agent.{name}")

    def _create_agent(self) -> AssistantAgent:
        """
        Create the AutoGen agent instance with proper LLM configuration.
        
        This method sets up the agent with either local or cloud-based LLM configuration
        based on the provided settings.
        """
        # Get model settings
        model = self.llm_config.get('model', 'gpt-4')
        
        # Create agent with specified LLM configuration
        return AssistantAgent(
            name=self.name,
            llm_config={
                "config_list": [{
                    "model": model,
                    "api_key": self.llm_config.get('api_key'),
                    "base_url": self.llm_config.get('base_url'),
                    "api_type": self.llm_config.get('api_type', 'openai'),
                    "api_version": self.llm_config.get('api_version'),
                }],
                "temperature": self.llm_config.get('temperature', 0.7),
                **{k: v for k, v in self.llm_config.items() if k not in ['config_list', 'temperature', 'model', 'api_key', 'base_url', 'api_type', 'api_version']}
            },
            system_message=self.system_message
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
        log_message = f"[{timestamp}] {self.name}: {message}"
        
        if level == "error":
            self.logger.error(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

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
                "agent": self.name,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            
        # Also notify the on_message callback if set
        if self.on_message:
            self.on_message(self.name, message, role)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data through the agent.
        
        This is a stub method that must be implemented by subclasses.
        It defines the interface for processing intents and returning results.

        Args:
            input_data (Dict[str, Any]): Input data to process

        Returns:
            Dict[str, Any]: Processed result
        """
        raise NotImplementedError("Subclasses must implement process()")

    async def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a device via MQTT.
        
        Args:
            device_id (str): ID of the device to check
            
        Returns:
            Optional[Dict[str, Any]]: Device status or None if error
        """
        if not self.mqtt_client:
            self.log("No MQTT client available", level="warning")
            return None
            
        try:
            return await self.mqtt_client.get_device_status(device_id)
        except Exception as e:
            self.log(f"Error getting device status: {str(e)}", level="error")
            return None

    async def execute_device_action(self, device_id: str, capability: str, value: Any) -> Dict[str, Any]:
        """
        Execute an action on a device via MQTT.
        
        Args:
            device_id (str): ID of the device to control
            capability (str): Capability to control (e.g., 'onoff', 'dim')
            value (Any): Value to set for the capability
            
        Returns:
            Dict[str, Any]: Status of the action
        """
        if not self.mqtt_client:
            self.log("No MQTT client available", level="warning")
            return {"status": "error", "message": "No MQTT client available"}
            
        try:
            action = {
                "device_id": device_id,
                "capability": capability,
                "value": value
            }
            return await self.mqtt_client.execute_action(action)
        except Exception as e:
            self.log(f"Error executing device action: {str(e)}", level="error")
            return {"status": "error", "message": str(e)} 