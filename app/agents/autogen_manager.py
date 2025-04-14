"""
AutoGen Manager for HomeyMind.

This module orchestrates the interaction between different AutoGen agents
to process user requests and control home automation.
"""

import autogen
import asyncio
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator
from datetime import datetime
import yaml
from .base_agent import BaseAgent
from .homey_assistant import HomeyAssistant
from .device_controller import DeviceController
from .intent_parser import IntentParser

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
        self.conversations: List[Dict[str, Any]] = []
        self.message_handler: Optional[Callable] = None
        self._initialize_agents()
        
    def set_message_handler(self, handler: Callable):
        """Set a handler for realtime message updates."""
        self.message_handler = handler
        
    def clear_message_handler(self):
        """Clear the message handler."""
        self.message_handler = None
        
    def _initialize_agents(self):
        """Initialize all AutoGen agents."""
        # Get the LLM configuration
        llm_config = self.config.get('autogen', {}).get('llm_config', {})
        
        # Initialize each agent with the LLM configuration
        self.agents['homey_assistant'] = HomeyAssistant(
            name="HomeyAssistant",
            llm_config=llm_config,
            system_message="You are a helpful home automation assistant.",
            on_message=self._log_conversation
        )
        
        self.agents['device_controller'] = DeviceController(
            name="DeviceController",
            llm_config=llm_config,
            system_message="You are a device control expert.",
            on_message=self._log_conversation
        )
        
        self.agents['intent_parser'] = IntentParser(
            name="IntentParser",
            llm_config=llm_config,
            system_message="You are an expert at parsing user intents.",
            on_message=self._log_conversation
        )

    def _log_conversation(self, agent_name: str, message: str, role: str = "assistant"):
        """Log a conversation message from an agent."""
        msg = {
            "role": role.lower(),
            "message": message,
            "agent": agent_name,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "is_subagent": True  # Mark all agent messages as sub-messages
        }
        
        # Only append to conversations if it's not a progress message
        if not message.startswith("Verwerken van") and not message.startswith("Genereren van") and not message.startswith("Uitvoeren van"):
            self.conversations.append(msg)
        
        # Send realtime update if handler is set
        if self.message_handler:
            self.message_handler(msg)
        
    def _clear_conversations(self):
        """Clear the conversation history for a new interaction."""
        self.conversations = []
        
    async def process_intent(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user intent through the agent pipeline.
        
        Args:
            intent_data (Dict[str, Any]): User intent data
            
        Returns:
            Dict[str, Any]: Processed response with conversation history
        """
        self._clear_conversations()
        
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
            
        # Add conversations to the response
        response['conversations'] = self.conversations
        return response 
    
    async def process_command(self, text: str) -> Dict[str, Any]:
        """
        Convenience method to process raw text input (e.g., from speech) 
        and route it through the full AutoGen pipeline.
        """
        intent_data = {'text': text}
        return await self.process_intent(intent_data)

    async def process_intent_streaming(self, intent_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming versie van process_intent die berichten yield per stap."""
        self._clear_conversations()
        queue = asyncio.Queue()
        sent_messages = set()  # Keep track of messages we've already sent

        def stream_handler(msg):
            queue.put_nowait(msg)

        self.set_message_handler(stream_handler)

        try:
            # Parse intent
            yield {
                "message": f"Verwerken van opdracht: {intent_data.get('text', '')}", 
                "role": "intent_parser", 
                "is_subagent": True,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            parsed_intent = await self.agents['intent_parser'].process(intent_data.get('text', ''))
            
            # Process queued messages from intent parsing
            while not queue.empty():
                msg = await queue.get()
                msg_id = f"{msg['role']}:{msg['message']}"
                if msg_id not in sent_messages:
                    sent_messages.add(msg_id)
                    yield msg
            
            # Process with main assistant
            yield {
                "message": "Genereren van antwoord...", 
                "role": "homey_assistant", 
                "is_subagent": True,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            assistant_response = await self.agents['homey_assistant'].process(parsed_intent)
            
            # Process queued messages from assistant
            while not queue.empty():
                msg = await queue.get()
                msg_id = f"{msg['role']}:{msg['message']}"
                if msg_id not in sent_messages:
                    sent_messages.add(msg_id)
                    yield msg
            
            # Process with device controller if needed
            if assistant_response.get("requires_device_action", False):
                yield {
                    "message": "Uitvoeren van apparaat commando's...", 
                    "role": "device_controller", 
                    "is_subagent": True,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                device_response = await self.agents['device_controller'].process({
                    'command': assistant_response.get('response', '')
                })
                assistant_response['device_action'] = device_response

                # Process queued messages from device controller
                while not queue.empty():
                    msg = await queue.get()
                    msg_id = f"{msg['role']}:{msg['message']}"
                    if msg_id not in sent_messages:
                        sent_messages.add(msg_id)
                        yield msg

            # Process any remaining queued messages
            while not queue.empty():
                msg = await queue.get()
                msg_id = f"{msg['role']}:{msg['message']}"
                if msg_id not in sent_messages:
                    sent_messages.add(msg_id)
                    yield msg

            # Send completion without duplicating the last message
            yield {
                "type": "complete",
                "response": assistant_response.get("response", ""),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }

        finally:
            self.clear_message_handler()
