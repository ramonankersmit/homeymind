import paho.mqtt.client as mqtt
import json
import yaml
import os
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

# Load MQTT configuration
config = load_config()
MQTT_CONFIG = {
    "host": config["mqtt"]["host"],
    "port": config["mqtt"]["port"],
    "username": config["mqtt"]["username"],
    "password": config["mqtt"]["password"],
    "topic_prefix": config["mqtt"]["topic_prefix"]
}

DISCOVERY_DURATION = 3
discovered = defaultdict(dict)

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
        
        # Process devices
        for device in devices:
            if "name" in device and "capabilities" in device:
                print(f"Device: {device['name']}")
                print(f"Capabilities: {', '.join(device['capabilities'])}")
                print("-" * 50)
        
        client.disconnect()
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        client.disconnect()

def discover_devices():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.username_pw_set(MQTT_CONFIG['username'], MQTT_CONFIG['password'])
    
    try:
        client.connect(MQTT_CONFIG['host'], MQTT_CONFIG['port'], 60)
        client.loop_forever()
    except Exception as e:
        print(f"Error: {str(e)}")

def build_device_map(devices):
    device_map = defaultdict(dict)
    for dev_id, data in devices.items():
        name = data.get("name", "").lower()
        parts = name.split()
        locatie = None
        apparaat = None

        for woord in parts:
            if woord in ["woonkamer", "keuken", "slaapkamer", "zolder"]:
                locatie = woord
            if woord in ["licht", "lamp", "gordijn", "verwarming"]:
                apparaat = "licht" if woord in ["licht", "lamp"] else woord

        if locatie and apparaat:
            device_map[locatie][apparaat] = dev_id

    return dict(device_map)

if __name__ == "__main__":
    discover_devices()
