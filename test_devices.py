import sys
import os
import yaml
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from utils.device_list import KNOWN_DEVICES, update_device_list
    logger.info("Successfully imported device_list module")
    
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    logger.info("Successfully loaded config")
    
    # Try to update device list
    logger.info("Attempting to update device list...")
    updated_devices = update_device_list(config)
    logger.info(f"Updated device list: {updated_devices}")
    
    # Format devices for display
    formatted_devices = []
    for device in updated_devices:
        if isinstance(device, str):
            formatted_devices.append({
                "name": device,
                "id": device,
                "type": "light" if "licht" in device.lower() else "switch"
            })
        else:
            formatted_devices.append(device)
    
    logger.info(f"Formatted devices: {formatted_devices}")
    
except Exception as e:
    logger.error(f"Error: {e}") 