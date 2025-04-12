import json
import os
import yaml
import paho.mqtt.client as mqtt
from time import sleep
from collections import defaultdict

def load_config():
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables in config
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.getenv(env_var)
            if config[key] is None:
                print(f"Environment variable {env_var} not set")
                raise ValueError(f"Environment variable {env_var} not set")
    
    return config

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        # Subscribe to device topics
        client.subscribe("homey/+/devices")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        devices = json.loads(msg.payload.decode())
        print(f"Received {len(devices)} devices")
        
        # Filter devices with onoff or dim capabilities
        filtered_devices = []
        for device in devices:
            if "capabilities" in device:
                if any(cap in device["capabilities"] for cap in ["onoff", "dim"]):
                    filtered_devices.append(device["name"].lower().replace(" ", "_"))
        
        print(f"Found {len(filtered_devices)} devices with onoff or dim capabilities")
        
        # Update system prompt
        with open("prompts/system_prompt.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find and replace the device list
        start_marker = "Bekende apparaten:\n"
        end_marker = "\n\n"
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker, start_idx)
        
        if start_idx > len(start_marker) and end_idx > start_idx:
            new_content = content[:start_idx] + "\n".join(filtered_devices) + content[end_idx:]
            with open("prompts/system_prompt.txt", "w", encoding="utf-8") as f:
                f.write(new_content)
            print("System prompt updated successfully")
        else:
            print("Could not find device list in system prompt")
        
        client.disconnect()
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        client.disconnect()

def main():
    config = load_config()
    username = config["mqtt"]["username"]
    password = config["mqtt"]["password"]
    host = config["mqtt"]["host"]
    port = config["mqtt"]["port"]
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.username_pw_set(username, password)
    
    try:
        client.connect(host, port, 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
