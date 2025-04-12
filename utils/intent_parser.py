import json
import re
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    ONOFF = "onoff"
    DIM = "dim"
    SWITCH_MODE = "switch_mode"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    device: str
    action: str
    action_type: ActionType
    value: Optional[Union[int, float, bool]] = None
    parameters: Optional[Dict] = None

def parse_intent(response: str) -> Optional[Intent]:
    """Parse intent from LLM response with enhanced validation."""
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
        
        # Determine action type
        action = parsed["action"].strip().lower()
        action_type = _determine_action_type(action)
        
        # Extract value if present
        value = None
        if "value" in parsed:
            value = _parse_value(parsed["value"], action_type)
            
        # Extract additional parameters
        parameters = {}
        for key, val in parsed.items():
            if key not in ["device", "action", "value"]:
                parameters[key] = val
                
        return Intent(
            device=device,
            action=action,
            action_type=action_type,
            value=value,
            parameters=parameters
        )
        
    except json.JSONDecodeError as e:
        print(f"[WARN] Fout bij JSON-decodering: {e}")
        return None
    except Exception as e:
        print(f"[WARN] Fout bij intent parsing: {e}")
        return None

def _determine_action_type(action: str) -> ActionType:
    """Determine the type of action from the action string."""
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
    """Parse and validate the value based on action type."""
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
    """Validate if the intent is valid for the current system."""
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