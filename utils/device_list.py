"""
Device List Management module for HomeyMind.

This module handles the discovery and management of Homey devices through MQTT.
It maintains a cache of known devices and provides functionality to update the list
from the MQTT broker.
"""

import os
import json
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from app.core.memory import recall, remember

# Cache file for device list
DEVICE_CACHE_FILE = "cache/devices.json"

@dataclass
class Device:
    name: str
    type: str
    capabilities: Dict[str, Any]
    status: Dict[str, Any]
    last_updated: datetime

# List of default devices
DEFAULT_DEVICES = [
    Device(
        name="licht woonkamer",
        type="light",
        capabilities={
            "onoff": True,
            "dim": True,
            "color": True
        },
        status=recall("device_status_licht_woonkamer") or {"on": False, "brightness": 100, "color": "white"},
        last_updated=datetime.now()
    ),
    Device(
        name="licht keuken",
        type="light",
        capabilities={
            "onoff": True,
            "dim": True
        },
        status=recall("device_status_licht_keuken") or {"on": False, "brightness": 100},
        last_updated=datetime.now()
    ),
    Device(
        name="thermostat",
        type="thermostat",
        capabilities={
            "temperature": True,
            "setpoint": True,
            "mode": True
        },
        status=recall("device_status_thermostat") or {"temperature": 20, "setpoint": 20, "mode": "auto"},
        last_updated=datetime.now()
    )
]

# Initialize KNOWN_DEVICES with default devices
KNOWN_DEVICES = DEFAULT_DEVICES.copy()

def load_devices_from_cache() -> List[str]:
    """
    Load devices from cache file if it exists.
    
    Returns:
        List[str]: List of device names loaded from cache, or empty list if cache doesn't exist
    """
    if os.path.exists(DEVICE_CACHE_FILE):
        try:
            with open(DEVICE_CACHE_FILE, "r") as f:
                data = json.load(f)
                return data.get("devices", [])
        except:
            return []
    return []

def save_devices_to_cache(devices: List[str]):
    """
    Save devices to cache file.
    
    Args:
        devices (List[str]): List of device names to save
    """
    os.makedirs(os.path.dirname(DEVICE_CACHE_FILE), exist_ok=True)
    with open(DEVICE_CACHE_FILE, "w") as f:
        json.dump({"devices": devices}, f)

def get_devices_from_mqtt(config: Dict) -> List[str]:
    """
    Get devices from MQTT broker.
    
    Args:
        config (Dict): Configuration dictionary containing MQTT settings
        
    Returns:
        List[str]: List of discovered device names
    """
    import paho.mqtt.client as mqtt
    from time import sleep
    
    devices = defaultdict(dict)
    client = None
    ready = False
    discovery_complete = False

    def on_connect(client, userdata, flags, rc):
        nonlocal ready
        if rc == 0:
            print("[OK] Connected to MQTT broker")
            # Subscribe to all device related topics
            client.subscribe("homey/#")
            ready = True

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            if topic.startswith("homey/devices/"):
                parts = topic.split('/')
                device_id = parts[2]
                
                if "info" not in devices[device_id]:
                    devices[device_id]["info"] = {}
                    devices[device_id]["capabilities"] = {}
                
                # Device name
                if len(parts) == 4 and parts[3] == "name":
                    payload = msg.payload.decode().strip('"')
                    devices[device_id]["info"]["name"] = payload
                    print(f"Found device: {payload}")
                
                # Device type/class
                elif len(parts) == 4 and parts[3] == "class":
                    payload = msg.payload.decode().strip('"')
                    devices[device_id]["info"]["type"] = payload
                
                # Capabilities
                elif len(parts) > 4 and parts[3] == "capabilities":
                    capability = parts[4]
                    if capability not in devices[device_id]["capabilities"]:
                        devices[device_id]["capabilities"][capability] = {}
                    
                    if len(parts) > 5:
                        field = parts[5]
                        payload = msg.payload.decode().strip('"')
                        devices[device_id]["capabilities"][capability][field] = payload
                
                # State/values
                elif len(parts) > 4 and parts[3] == "state":
                    capability = parts[4]
                    if "state" not in devices[device_id]:
                        devices[device_id]["state"] = {}
                    devices[device_id]["state"][capability] = msg.payload.decode()

        except Exception as e:
            print(f"[ERROR] Error processing message: {e}")

    client = mqtt.Client()
    if "username" in config["mqtt"] and "password" in config["mqtt"]:
        client.username_pw_set(config["mqtt"]["username"], config["mqtt"]["password"])
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
        client.loop_start()
        
        # Wait for connection
        timeout = 10
        while timeout > 0 and not ready:
            sleep(1)
            timeout -= 1
            
        if not ready:
            print("[ERROR] Timeout waiting for MQTT connection")
            return []
            
        # Wait longer for device messages (30 seconds)
        print("Waiting for Homey device messages...")
        sleep(30)
        client.loop_stop()
        client.disconnect()
        
        # Process and format devices
        formatted_devices = []
        for device_id, data in devices.items():
            if "info" not in data or "name" not in data["info"]:
                continue
                
            device = {
                "id": device_id,
                "name": data["info"]["name"],
                "type": data["info"].get("type", "unknown"),
                "capabilities": list(data.get("capabilities", {}).keys()),
                "state": {}
            }
            
            # Add state information
            if "state" in data:
                device["state"] = {
                    k: v for k, v in data["state"].items()
                    if not (v.startswith('{') or v.startswith('['))  # Filter out complex JSON values
                }
            
            formatted_devices.append(device)
            print(f"Added device: {device['name']} ({len(device['capabilities'])} capabilities)")
        
        # Save to cache
        save_devices_to_cache(formatted_devices)
        return formatted_devices
        
    except Exception as e:
        print(f"[ERROR] Error connecting to MQTT: {e}")
        return []

def update_device_list(config: Dict) -> List[Device]:
    """
    Update the device list from MQTT and return the new list.
    
    Args:
        config (Dict): Configuration dictionary containing MQTT settings
        
    Returns:
        List[Device]: Updated list of devices
    """
    global KNOWN_DEVICES
    try:
        mqtt_devices = get_devices_from_mqtt(config)
        if mqtt_devices:
            # Convert MQTT devices to Device objects
            KNOWN_DEVICES = [
                Device(
                    name=device_name,
                    type="light" if "licht" in device_name.lower() else "switch",
                    capabilities={"onoff": True},
                    status=recall(f"device_status_{device_name}") or {"on": False},
                    last_updated=datetime.now()
                )
                for device_name in mqtt_devices
            ]
        else:
            print("[INFO] Using default devices as MQTT fetch failed")
            KNOWN_DEVICES = DEFAULT_DEVICES.copy()
    except Exception as e:
        print(f"[ERROR] Error updating device list: {e}")
        print("[INFO] Falling back to default devices")
        KNOWN_DEVICES = DEFAULT_DEVICES.copy()
    
    return KNOWN_DEVICES

def get_device(name: str) -> Optional[Device]:
    """
    Get a device by name.
    
    Args:
        name (str): Name of the device.
        
    Returns:
        Optional[Device]: Device if found, None otherwise.
    """
    for device in KNOWN_DEVICES:
        if device.name.lower() == name.lower():
            return device
    return None

def get_device_status(name: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a device.
    
    Args:
        name (str): Name of the device.
        
    Returns:
        Optional[Dict[str, Any]]: Device status if found, None otherwise.
    """
    device = get_device(name)
    if device:
        return device.status
    return None

def update_device_status(name: str, status: Dict[str, Any]):
    """
    Update the status of a device.
    
    Args:
        name (str): Name of the device.
        status (Dict[str, Any]): New status of the device.
    """
    device = get_device(name)
    if device:
        device.status.update(status)
        device.last_updated = datetime.now()
        remember("device_status_" + name.replace(" ", "_").lower(), device.status)