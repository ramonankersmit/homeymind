import sys
import os
from pathlib import Path
import json
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import AsyncGenerator, List, Dict, Optional
import yaml
import logging
from datetime import datetime
from paho.mqtt import client as mqtt_client
from dotenv import load_dotenv

# Load environment variables from root .env file
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
CONFIG_DIR = Path(__file__).parent / "config"
DEVICES_CONFIG_FILE = CONFIG_DIR / "devices.json"
MQTT_BROKER = os.getenv("HOMEY_HOST", "localhost")
MQTT_PORT = int(os.getenv("HOMEY_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC = "homey/#"
MQTT_REQUEST_TOPIC = "homey/request_devices"
MQTT_CLIENT_ID = "homeymind_backend"
MQTT_TIMEOUT = 10  # seconds

# Device type mapping
DEVICE_TYPE_MAPPING = {
    "boolean": "Schakelaar",
    "number": "Sensor",
    "enum": "Keuzemenu",
    "string": "Tekst",
    "light": "Lamp",
    "blinds": "Zonwering",
    "speaker": "Speaker",
    "thermostat": "Thermostaat"
}

logger.info(f"Using MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")

# Create demo devices
DEMO_DEVICES = [
    {
        "id": "demo1",
        "name": "[Demo] Woonkamer Lamp",
        "type": "light",
        "capabilities": ["onoff", "dim"],
        "state": {
            "onoff": True,
            "dim": 80
        }
    },
    {
        "id": "demo2",
        "name": "[Demo] Thermostaat",
        "type": "thermostat",
        "capabilities": ["target_temperature", "measure_temperature"],
        "state": {
            "target_temperature": 21.5,
            "measure_temperature": 20.8
        }
    },
    {
        "id": "demo3",
        "name": "[Demo] Bewegingssensor",
        "type": "sensor",
        "capabilities": ["alarm_motion", "measure_battery"],
        "state": {
            "alarm_motion": False,
            "measure_battery": 85
        }
    },
    {
        "id": "demo4",
        "name": "[Demo] TV",
        "type": "tv",
        "capabilities": ["onoff", "volume_set"],
        "state": {
            "onoff": False,
            "volume_set": 35
        }
    },
    {
        "id": "demo5",
        "name": "[Demo] Rolluik Slaapkamer",
        "type": "blinds",
        "capabilities": ["windowcoverings_set", "measure_battery"],
        "state": {
            "windowcoverings_set": 100,
            "measure_battery": 90
        }
    }
]

# Ensure config directory exists
CONFIG_DIR.mkdir(exist_ok=True)

# Initialize empty config file with demo devices if it doesn't exist
if not DEVICES_CONFIG_FILE.exists():
    with open(DEVICES_CONFIG_FILE, 'w') as f:
        json.dump({"demo_devices": DEMO_DEVICES, "actual_devices": []}, f, indent=2)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track MQTT connection state
mqtt_connected = False
mqtt_last_error = None
mqtt_message_count = 0
actual_devices = {}

def load_devices_config() -> Dict:
    """Load devices from config file, create with demo devices if doesn't exist."""
    try:
        if DEVICES_CONFIG_FILE.exists():
            with open(DEVICES_CONFIG_FILE, 'r') as f:
                return json.load(f)
        else:
            # Return empty config if file doesn't exist
            return {"demo_devices": [], "actual_devices": []}
    except Exception as e:
        logger.error(f"Error loading devices config: {e}")
        return {"demo_devices": [], "actual_devices": []}

def save_devices_config(config: Dict):
    """Save devices config to file."""
    try:
        with open(DEVICES_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving devices config: {e}")
        raise HTTPException(status_code=500, detail="Error saving devices configuration")

def on_mqtt_connect(client, userdata, flags, rc):
    """Callback when the MQTT client connects."""
    global mqtt_connected
    connection_codes = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorised"
    }
    
    if rc == 0:
        logger.info("Connected to MQTT broker successfully")
        mqtt_connected = True
        mqtt_last_error = None
        client.subscribe([(MQTT_TOPIC, 1), (MQTT_REQUEST_TOPIC, 1)])
        logger.info(f"Subscribed to topics: {MQTT_TOPIC}, {MQTT_REQUEST_TOPIC}")
    else:
        error_msg = f"Failed to connect to MQTT broker: {connection_codes.get(rc, f'Unknown error {rc}')}"
        logger.error(error_msg)
        mqtt_connected = False
        mqtt_last_error = error_msg

def on_mqtt_disconnect(client, userdata, rc):
    global mqtt_connected, mqtt_last_error
    mqtt_connected = False
    error_msg = f"Disconnected from MQTT broker with code: {rc}"
    logger.error(error_msg)
    mqtt_last_error = error_msg

def on_mqtt_message(client, userdata, msg):
    """Callback when an MQTT message is received."""
    global mqtt_message_count, actual_devices
    try:
        mqtt_message_count += 1
        logger.debug(f"Received MQTT message #{mqtt_message_count} on topic: {msg.topic}")
        
        # Parse device information from topic
        if msg.topic.startswith("homey/devices/"):
            parts = msg.topic.split("/")
            if len(parts) >= 4:
                device_id = parts[2]
                
                if device_id not in actual_devices:
                    actual_devices[device_id] = {
                        "id": device_id,
                        "name": "",
                        "type": "",
                        "capabilities": [],  # Initialize as empty array
                        "state": {}
                    }
                
                # Update device information based on topic type
                if "name" in msg.topic:
                    actual_devices[device_id]["name"] = msg.payload.decode().strip('"')
                elif "type" in msg.topic:
                    raw_type = msg.payload.decode().strip('"')
                    # Map the raw type to a user-friendly name, or use the raw type if no mapping exists
                    actual_devices[device_id]["type"] = DEVICE_TYPE_MAPPING.get(raw_type, raw_type)
                elif "capabilities" in msg.topic:
                    # Extract capability name from topic
                    capability_parts = msg.topic.split("/")
                    if len(capability_parts) >= 5:
                        capability_name = capability_parts[4]
                        if capability_name not in actual_devices[device_id]["capabilities"]:
                            actual_devices[device_id]["capabilities"].append(capability_name)
                elif "state" in msg.topic:
                    try:
                        state = json.loads(msg.payload.decode())
                        actual_devices[device_id]["state"].update(state)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse state: {msg.payload.decode()}")
                
                logger.info(f"Updated device {device_id}: {actual_devices[device_id]}")
                
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

# Initialize MQTT client
mqtt_client = mqtt_client.Client(MQTT_CLIENT_ID)
if MQTT_USERNAME and MQTT_PASSWORD:
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_mqtt_connect
mqtt_client.on_message = on_mqtt_message
mqtt_client.on_disconnect = on_mqtt_disconnect

# Enable MQTT debug logging
mqtt_client.enable_logger(logger)

try:
    logger.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
    mqtt_client.loop_start()
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    mqtt_last_error = str(e)

@app.get("/devices")
async def get_devices():
    """Get all devices (both demo and actual)."""
    config = load_devices_config()
    demo_devices = config.get("demo_devices", [])
    
    # Only show demo devices if there are no actual devices or MQTT is not connected
    if not mqtt_connected or len(actual_devices) == 0:
        return {
            "devices": demo_devices,
            "status": {
                "mqtt_connected": mqtt_connected,
                "mqtt_messages_received": mqtt_message_count,
                "demo_device_count": len(demo_devices),
                "actual_device_count": len(actual_devices),
                "using_demo_devices": True
            },
            "warnings": [
                "Geen verbinding met MQTT broker" if not mqtt_connected else "Geen actieve apparaten gevonden"
            ]
        }
    
    # Return only actual devices when MQTT is connected and devices are found
    return {
        "devices": list(actual_devices.values()),
        "status": {
            "mqtt_connected": mqtt_connected,
            "mqtt_messages_received": mqtt_message_count,
            "demo_device_count": len(demo_devices),
            "actual_device_count": len(actual_devices),
            "using_demo_devices": False
        }
    }

@app.post("/devices/refresh")
async def refresh_devices():
    """Trigger a refresh of devices via MQTT."""
    try:
        if not mqtt_connected:
            raise HTTPException(
                status_code=503,
                detail="Geen verbinding met MQTT broker"
            )
            
        # Publish a request for devices update
        mqtt_client.publish(
            MQTT_REQUEST_TOPIC,
            json.dumps({"action": "refresh", "timestamp": datetime.now().isoformat()}),
            qos=1
        )
        return {"status": "success", "message": "Device refresh requested"}
    except Exception as e:
        logger.error(f"Error refreshing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup MQTT client on shutdown
@app.on_event("shutdown")
def cleanup():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
