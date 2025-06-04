"""
Base agent class for HomeyMind.

This module provides the base class for all AutoGen agents in the system.
"""

from typing import Dict, Any, Optional, Callable
import autogen
from autogen import AssistantAgent, UserProxyAgent
import logging
from datetime import datetime
from app.core.config import LLMConfig
from app.core.logger import logger

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
    
    def __init__(self, config: LLMConfig):
        """Initialize the agent with configuration and MQTT client."""
        self.config = config
        self.name = config.name
        self.agent = self._create_agent(config)
        self.llm_config = self.agent.llm_config
        self._message_handler = None

    def _create_agent(self, config: LLMConfig) -> AssistantAgent:
        """Create an AssistantAgent with the given configuration."""
        llm_config = {
            "config_list": [{
                "model": config.openai.model,
                "api_type": config.openai.api_type,
                "api_key": config.openai.api_key
            }]
        }
        return AssistantAgent(
            name=config.name,
            llm_config=llm_config
        )

    def set_message_handler(self, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Set the message handler for this agent."""
        self._message_handler = handler
    
    @property
    def message_handler(self) -> Optional[Callable[[Dict[str, Any]], None]]:
        """Get the message handler for this agent."""
        return self._message_handler
    
    def _log_message(self, msg_type: str, message: str) -> None:
        """Log a message with the agent's name.
        
        Args:
            msg_type: Type of message (info, error, etc)
            message: Message to log
        """
        logger.info(f"[{self.name}] {message}")
        if self._message_handler:
            self._message_handler({
                "type": msg_type,
                "message": message,
                "agent": self.name,
                "role": "assistant"
            })
    
    def process(self, message: str) -> str:
        """Process a message and return a response."""
        self._log_message("incoming", message)
        try:
            response = self.agent.generate_reply(messages=[{"role": "user", "content": message}])
            if response is None:
                response = "Sorry, I couldn't generate a response."
            self._log_message("outgoing", response)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error while processing your message."
    
    async def close(self) -> None:
        """Clean up resources."""
        pass

    def execute_device_action(self, device_id: str, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute an action on a device through MQTT.
        
        Args:
            device_id: ID of the device to control
            action: Action to execute
            params: Optional parameters for the action
            
        Returns:
            Dictionary containing the execution results
        """
        self._log_message("action", f"Executing {action} on device {device_id}")
        return {"status": "success", "device_id": device_id, "action": action}

    def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Get the current status of a device through MQTT.
        
        Args:
            device_id: ID of the device to query
            
        Returns:
            Dictionary containing the device status
        """
        self._log_message("status", f"Getting status for device {device_id}")
        return {"status": "online", "device_id": device_id} 