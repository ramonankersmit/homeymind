"""
Intent Parser module for HomeyMind.

This module provides functionality for parsing and validating user intents from LLM responses.
It handles the conversion of natural language commands into structured device control actions.
"""

import json
import re
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
from .capability_manager import CapabilityManager

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

def parse_intent(response: str) -> Optional[Intent]:
    """
    Parse intent from LLM response with enhanced validation.
    
    Args:
        response (str): The LLM response containing the intent
        
    Returns:
        Optional[Intent]: The parsed intent, or None if parsing fails
        
    This function:
    1. Extracts JSON from the LLM response
    2. Validates required fields
    3. Normalizes device names
    4. Determines device types and validates actions
    5. Extracts values and parameters
    """
    # Initialize capability manager
    capability_manager = CapabilityManager()
    
    # Zoek eerste JSON-achtig blok uit LLM-respons
    match = re.search(r'\{.*?\}', response, re.DOTALL)
    if not match:
        print("[WARN] Geen JSON-herkenning in respons")
        return None
        
    try:
        parsed = json.loads(match.group(0))
        
        # Validate required fields
        if not all(key in parsed for key in ["device", "action"]):
            print("[WARN] JSON mist vereiste velden")
            return None
            
        # Normalize device name
        device = parsed["device"].strip().lower().replace(" ", "_")
        
        # Determine device type and validate action
        device_type = capability_manager.get_device_type(device)
        if not device_type:
            print(f"[WARN] Onbekend apparaattype: {device}")
            return None
            
        action = parsed["action"].strip().lower()
        if not capability_manager.validate_action(device_type, action):
            print(f"[WARN] Ongeldige actie voor apparaattype: {action}")
            return None
            
        # Determine action type based on device type
        if device_type == "licht":
            if "dim" in action:
                action_type = ActionType.DIM
            else:
                action_type = ActionType.ONOFF
        elif device_type == "gordijn":
            action_type = ActionType.WINDOWCOVERINGS
        elif device_type == "airco":
            action_type = ActionType.THERMOSTAT
        else:
            action_type = ActionType.UNKNOWN
            
        # Extract value if present
        value = None
        if "value" in parsed:
            value = _parse_value(parsed["value"], action_type)
            
        # Extract additional parameters
        parameters = {}
        if action_type == ActionType.DIM:
            parameters["direction"] = capability_manager.get_capability_payload(device_type, "dim", action)
        elif action_type == ActionType.WINDOWCOVERINGS:
            parameters["state"] = capability_manager.get_capability_payload(device_type, "windowcoverings_state", action)
        elif action_type == ActionType.THERMOSTAT:
            parameters["mode"] = capability_manager.get_capability_payload(device_type, "thermostat_mode", action)
        else:
            parameters["state"] = capability_manager.get_capability_payload(device_type, "onoff", action)
            
        return Intent(device, action, action_type, value, parameters)
        
    except Exception as e:
        print(f"[ERROR] Fout bij parsen intent: {e}")
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