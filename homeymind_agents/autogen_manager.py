"""
AutoGen Manager for HomeyMind.

This module manages the AutoGen framework integration and agent coordination.
"""

import autogen
from typing import Dict, Any, Optional
from .agents import HomeyAssistant, DeviceController, IntentParser

class AutoGenManager: 
    """Manages the AutoGen framework integration for HomeyMind."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AutoGen manager.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary
        """
        self.config = config
        self.agents: Dict[str, Any] = {}
        self._initialize_agents()
        
    def _initialize_agents(self):
        """Initialize all AutoGen agents."""
        # Get the LLM configuration
        llm_config = self.config.get('autogen', {}).get('llm_config', {})
        
        # Initialize each agent with the LLM configuration
        self.agents['homey_assistant'] = HomeyAssistant(
            name="HomeyAssistant",
            llm_config=llm_config,
            system_message="You are a helpful home automation assistant."
        )
        
        self.agents['device_controller'] = DeviceController(
            name="DeviceController",
            llm_config=llm_config,
            system_message="You are a device control expert."
        )
        
        self.agents['intent_parser'] = IntentParser(
            name="IntentParser",
            llm_config=llm_config,
            system_message="You are an expert at parsing user intents."
        )
        
    async def process_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user intent through the agent pipeline.
        
        Args:
            intent_data (Dict[str, Any]): User intent data
            
        Returns:
            Dict[str, Any]: Processed response
        """
        # First parse the intent
        print(f"Processing intent: {intent_data}")
        parsed_intent = await self.agents['intent_parser'].process(intent_data.get('text', ''))
        
        # Then process with the main assistant
        response = await self.agents['homey_assistant'].process(parsed_intent)
        
        # If device action is needed, use the device controller
        if response.get('requires_device_action', False):
            device_response = await self.agents['device_controller'].process({
                'command': response.get('response', '')
            })
            response['device_action'] = device_response
            
        return response 
    
    async def process_command(self, text: str) -> Dict[str, Any]:
        """
        Convenience method to process raw text input (e.g., from speech) 
        and route it through the full AutoGen pipeline.
        """
        intent_data = {'text': text}
        return await self.process_intent(intent_data)