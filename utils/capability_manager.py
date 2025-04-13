import json
import os
import yaml
from typing import Dict, List, Optional, Union

class CapabilityManager:
    """
    Manages device capabilities and command mappings for the HomeyMind system.
    
    This class handles:
    - Loading device type configurations from YAML
    - Determining device types based on keywords
    - Managing capabilities and their payloads
    - Validating actions against device capabilities
    
    The configuration is loaded from a YAML file that defines:
    - Device types (e.g., 'licht', 'gordijn', 'airco')
    - Keywords for identifying device types
    - Capabilities for each device type
    - Action-to-payload mappings for each capability
    """
    
    def __init__(self, config_path: str = "utils/device_types.yaml"):
        """
        Initialize the CapabilityManager.
        
        Args:
            config_path (str): Path to the YAML configuration file containing
                             device types and capabilities.
        """
        self.config_path = config_path
        self.device_types = self._load_config()
        
    def _load_config(self) -> Dict:
        """
        Load device types and capabilities from the YAML configuration file.
        
        Returns:
            Dict: Dictionary containing device type configurations.
                 Returns empty dict if file doesn't exist or on error.
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    config = yaml.safe_load(f)
                    return config.get("device_types", {})
            except Exception as e:
                print(f"[ERROR] Fout bij laden configuratie: {e}")
                return {}
        return {}
    
    def get_device_type(self, device_name: str) -> Optional[str]:
        """
        Determine the device type based on the device name.
        
        Args:
            device_name (str): Name of the device to identify.
            
        Returns:
            Optional[str]: Device type if found (e.g., 'licht', 'gordijn'),
                         None if no matching type found.
        """
        device_name = device_name.lower()
        for device_type, config in self.device_types.items():
            if any(keyword in device_name for keyword in config["keywords"]):
                return device_type
        return None
    
    def get_capability_payload(self, device_type: str, capability: str, action: str) -> Optional[str]:
        """
        Get the MQTT payload for a specific action on a device capability.
        
        Args:
            device_type (str): Type of device (e.g., 'licht', 'gordijn').
            capability (str): Capability to use (e.g., 'onoff', 'dim').
            action (str): Action to perform (e.g., 'aanzetten', 'uitzetten').
            
        Returns:
            Optional[str]: MQTT payload for the action if valid,
                         None if device type, capability, or action is invalid.
        """
        if device_type not in self.device_types:
            return None
            
        device_config = self.device_types[device_type]
        if capability not in device_config["capabilities"]:
            return None
            
        cap_config = device_config["capabilities"][capability]
        if not cap_config.get("settable", False):
            return None
            
        return cap_config["payloads"].get(action.lower())
    
    def get_supported_actions(self, device_type: str) -> List[str]:
        """
        Get all supported actions for a device type.
        
        Args:
            device_type (str): Type of device to get actions for.
            
        Returns:
            List[str]: List of supported actions for the device type.
                     Returns empty list if device type is invalid.
        """
        if device_type not in self.device_types:
            return []
            
        actions = []
        for cap, config in self.device_types[device_type]["capabilities"].items():
            if config.get("settable", False):
                actions.extend(config["payloads"].keys())
        return actions
    
    def validate_action(self, device_type: str, action: str) -> bool:
        """
        Check if an action is valid for a device type.
        
        Args:
            device_type (str): Type of device to validate action for.
            action (str): Action to validate.
            
        Returns:
            bool: True if action is valid for the device type, False otherwise.
        """
        return action.lower() in self.get_supported_actions(device_type)
    
    def get_capabilities(self, device_type: str) -> Dict:
        """
        Get all capabilities for a device type.
        
        Args:
            device_type (str): Type of device to get capabilities for.
            
        Returns:
            Dict: Dictionary of capabilities for the device type.
                 Returns empty dict if device type is invalid.
        """
        if device_type not in self.device_types:
            return {}
        return self.device_types[device_type]["capabilities"] 