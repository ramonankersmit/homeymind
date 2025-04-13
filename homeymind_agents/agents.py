"""
AutoGen agents for HomeyMind.

This module implements specialized agents using the AutoGen framework
for different aspects of home automation.
"""

import autogen
from typing import Dict, Any
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

    def __init__(self, name: str, llm_config: Dict[str, Any], system_message: str):
        """
        Initialize a base agent.

        Args:
            name (str): Name of the agent
            llm_config (Dict[str, Any]): LLM configuration
            system_message (str): System message defining the agent's role
        """
        self.name = name
        self.llm_config = llm_config
        self.system_message = system_message
        self.agent = self._create_agent()

    def _create_agent(self) -> AssistantAgent:
        """Create the AutoGen agent instance."""
        return AssistantAgent(
            name=self.name,
            llm_config=self.llm_config,
            system_message=self.system_message
        )

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data through the agent.

        Args:
            input_data (Dict[str, Any]): Input data to process

        Returns:
            Dict[str, Any]: Processed result
        """
        raise NotImplementedError("Subclasses must implement process()")


class HomeyAssistant(BaseAgent):
    """Main assistant agent for HomeyMind."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate intents, provide responses."""
        user_proxy = create_user_proxy()

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=input_data.get('text', ''),
            clear_history=True
        )

        return {
            'response': chat_result.summary,
            'requires_device_action': 'device_action' in chat_result.summary.lower()
        }


class DeviceController(BaseAgent):
    """Agent responsible for controlling home devices."""

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_proxy = create_user_proxy()

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=f"Execute device control: {input_data.get('command', '')}",
            clear_history=True
        )

        return {
            'action': chat_result.summary,
            'status': 'success' if 'success' in chat_result.summary.lower() else 'failed'
        }


class IntentParser(BaseAgent):
    """Agent responsible for parsing user intents."""

    async def process(self, input_data: str) -> Dict[str, Any]:
        user_proxy = create_user_proxy()

        chat_result = user_proxy.initiate_chat(
            self.agent,
            message=f"Parse this command into intent: {input_data}",
            clear_history=True
        )

        return {
            'text': input_data,
            'intent': chat_result.summary,
            'confidence': 0.9  # Placeholder for later evaluation
        }
