"""
Intent Parser module for HomeyMind.

This module provides functionality for parsing and validating user intents from LLM responses.
It handles the conversion of natural language commands into structured device control actions.
"""

import json
import re
from typing import Dict, Optional, Union, List, Any
from dataclasses import dataclass
from enum import Enum
from .capability_manager import CapabilityManager
from llm_manager import LLMManager

class ActionType(Enum):
    """
    Enumeration of possible action types in the system.
    
    Attributes:
        ONOFF: Basic on/off control
        DIM: Dimming control
        WINDOWCOVERINGS: Window covering control
        THERMOSTAT: Thermostat control
        SWITCH_MODE: Mode switching (e.g., LLM mode)
        UNKNOWN: Unknown or unsupported action type
    """
    ONOFF = "onoff"
    DIM = "dim"
    WINDOWCOVERINGS = "windowcoverings"
    THERMOSTAT = "thermostat"
    SWITCH_MODE = "switch_mode"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """
    Data class representing a parsed user intent.
    
    Attributes:
        device (str): The target device name
        action (str): The action to perform
        action_type (ActionType): The type of action
        value (Optional[Union[int, float, bool]]): Optional value for the action
        parameters (Optional[Dict]): Additional parameters for the action
    """
    device: str
    action: str
    action_type: ActionType
    value: Optional[Union[int, float, bool]] = None
    parameters: Optional[Dict] = None

def parse_intent(text: str, llm_manager: Optional[LLMManager] = None) -> Optional[Dict[str, Any]]:
    """
    Parse the intent from the given text.
    
    Args:
        text (str): The text to parse.
        llm_manager (Optional[LLMManager]): The LLM manager to use for parsing.
        
    Returns:
        Optional[Dict[str, Any]]: The parsed intent, or None if parsing failed.
    """
    if not llm_manager:
        # Simple intent parsing for testing
        text = text.lower()
        
        # Temperature control
        if any(word in text for word in ["koud", "warm", "temperatuur"]):
            return {
                "type": "temperature",
                "action": "set_temperature",
                "device": "thermostat",
                "value": 20 if "koud" in text else 18
            }
        
        # Light control
        if any(word in text for word in ["licht", "lamp"]):
            return {
                "type": "light",
                "action": "turn_on" if "aan" in text else "turn_off",
                "device": "licht " + ("woonkamer" if "woonkamer" in text else "keuken")
            }
        
        return None
    
    # Use LLM for intent parsing
    with open("prompts/intent_recognition.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    prompt = f"""{system_prompt}

Gebruiker: {text}
Antwoord:"""
    
    response = llm_manager.ask(prompt)
    
    # Parse the response into an intent
    # This is a simplified version - in reality you'd want to use a more robust parser
    try:
        # The response should be in JSON format
        intent = json.loads(response)
        return intent
    except:
        return None

def _determine_action_type(action: str) -> ActionType:
    """
    Determine the type of action from the action string.
    
    Args:
        action (str): The action string to analyze
        
    Returns:
        ActionType: The determined action type
    """
    action = action.lower()
    
    if action in ["aan", "uit", "on", "off", "toggle"]:
        return ActionType.ONOFF
    elif action in ["dim", "helderder", "donkerder", "brightness"]:
        return ActionType.DIM
    elif action == "switch_mode":
        return ActionType.SWITCH_MODE
    else:
        return ActionType.UNKNOWN

def _parse_value(value: Union[str, int, float], action_type: ActionType) -> Optional[Union[int, float, bool]]:
    """
    Parse and validate the value based on action type.
    
    Args:
        value (Union[str, int, float]): The value to parse
        action_type (ActionType): The type of action
        
    Returns:
        Optional[Union[int, float, bool]]: The parsed value, or None if parsing fails
    """
    try:
        if action_type == ActionType.ONOFF:
            if isinstance(value, str):
                value = value.lower()
                if value in ["aan", "on", "true", "1"]:
                    return True
                elif value in ["uit", "off", "false", "0"]:
                    return False
            elif isinstance(value, bool):
                return value
            elif isinstance(value, (int, float)):
                return bool(value)
        elif action_type == ActionType.DIM:
            if isinstance(value, str):
                # Try to convert percentage to float
                if "%" in value:
                    value = value.replace("%", "").strip()
                return float(value) / 100.0
            elif isinstance(value, (int, float)):
                return float(value) / 100.0
        return None
    except:
        return None

def validate_intent(intent: Intent, known_devices: List[str]) -> bool:
    """
    Validate if the intent is valid for the current system.
    
    Args:
        intent (Intent): The intent to validate
        known_devices (List[str]): List of known device names
        
    Returns:
        bool: True if the intent is valid, False otherwise
    """
    if not intent:
        return False
        
    # Check if device is known
    if intent.device not in known_devices:
        print(f"[WARN] Onbekend apparaat: {intent.device}")
        return False
        
    # Validate action type
    if intent.action_type == ActionType.UNKNOWN:
        print(f"[WARN] Onbekende actie: {intent.action}")
        return False
        
    # Validate value if present
    if intent.value is not None:
        if intent.action_type == ActionType.DIM:
            if not (0 <= intent.value <= 1):
                print(f"[WARN] Ongeldige dimwaarde: {intent.value}")
                return False
                
    return True