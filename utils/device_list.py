"""
Device List Management module for HomeyMind.

This module handles the discovery and management of Homey devices through MQTT.
It maintains a cache of known devices and provides functionality to update the list
from the MQTT broker.
"""

import os
import json
from typing import List, Dict
from collections import defaultdict

# Cache file for device list
DEVICE_CACHE_FILE = "cache/devices.json"

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
        
    This function:
    1. Connects to the MQTT broker
    2. Subscribes to device topics
    3. Collects device information
    4. Filters for devices with onoff or dim capabilities
    5. Saves the list to cache
    """
    import paho.mqtt.client as mqtt
    from time import sleep
    
    devices = defaultdict(dict)
    client = None
    ready = False

    def on_connect(client, userdata, flags, rc):
        nonlocal ready
        if rc == 0:
            print("[OK] Connected to MQTT broker")
            client.subscribe("homey/devices/+/name")  # Get device names
            client.subscribe("homey/devices/+/capabilities/+/name")  # Get capability names
            client.subscribe("homey/devices/+/capabilities/+/value")  # Get capability values
            ready = True

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            if topic.startswith("homey/devices/"):
                parts = topic.split('/')
                device_id = parts[2]
                
                if "info" not in devices[device_id]:
                    devices[device_id]["info"] = {}
                
                if len(parts) == 4 and parts[3] == "name":
                    payload = msg.payload.decode().strip('"')
                    devices[device_id]["info"]["name"] = payload
                    print(f"Found device: {payload}")
                elif len(parts) > 4 and parts[3] == "capabilities":
                    capability = parts[4]
                    field = parts[5]
                    
                    if capability not in devices[device_id]:
                        devices[device_id][capability] = {}
                    
                    if field == "name":
                        payload = msg.payload.decode().strip('"')
                        devices[device_id][capability]["name"] = payload
                    elif field == "value":
                        payload = msg.payload.decode()
                        devices[device_id][capability]["value"] = payload
        except Exception as e:
            print(f"[ERROR] Error processing message: {e}")

    client = mqtt.Client()
    client.username_pw_set(config["mqtt"]["username"], config["mqtt"]["password"])
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
        client.loop_start()
        
        # Wait for connection and messages
        timeout = 10
        while timeout > 0 and not ready:
            sleep(1)
            timeout -= 1
            
        if not ready:
            print("[ERROR] Timeout waiting for MQTT connection")
            return []
            
        # Wait for device messages
        print("Waiting for Homey device messages...")
        sleep(15)  # Wait for device messages
        client.loop_stop()
        client.disconnect()
        
        # Process devices
        device_list = []
        for device_id, data in devices.items():
            device_name = data.get("info", {}).get("name", "").lower().replace(" ", "_")
            if not device_name:
                continue
                
            # Only include devices with onoff or dim capability
            if "onoff" in data or "dim" in data:
                device_list.append(device_name)
                print(f"Added device: {device_name}")
        
        # Save to cache
        save_devices_to_cache(device_list)
        return sorted(device_list)
    except Exception as e:
        print(f"[ERROR] Error connecting to MQTT: {e}")
        return []

# Load devices from cache initially
KNOWN_DEVICES = load_devices_from_cache()

def update_device_list(config: Dict) -> List[str]:
    """
    Update the device list from MQTT and return the new list.
    
    Args:
        config (Dict): Configuration dictionary containing MQTT settings
        
    Returns:
        List[str]: Updated list of device names
    """
    global KNOWN_DEVICES
    KNOWN_DEVICES = get_devices_from_mqtt(config)
    return KNOWN_DEVICES