"""
Base agent class for HomeyMind.

This module provides the base class for all AutoGen agents in the system.
"""

from typing import Dict, Any, Optional, Callable
import autogen
from autogen import AssistantAgent, UserProxyAgent


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

    def __init__(self, name: str, llm_config: Dict[str, Any], system_message: str, on_message: Optional[Callable] = None):
        """
        Initialize a base agent.

        Args:
            name (str): Name of the agent
            llm_config (Dict[str, Any]): LLM configuration
            system_message (str): System message defining the agent's role
            on_message (Optional[Callable]): Callback for logging messages
        """
        self.name = name
        self.llm_config = llm_config
        self.system_message = system_message
        self.on_message = on_message
        self.agent = self._create_agent()

    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen agent instance."""
        return AssistantAgent(
            name=self.name,
            llm_config=self.llm_config,
            system_message=self.system_message
        )

    def _log_message(self, message: str, role: str = "assistant"):
        """Log a message if callback is provided."""
        if self.on_message:
            print(f"Logging message from {self.name}: {message}")
            self.on_message(self.name, message, role)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data through the agent.

        Args:
            input_data (Dict[str, Any]): Input data to process

        Returns:
            Dict[str, Any]: Processed result
        """
        raise NotImplementedError("Subclasses must implement process()") 