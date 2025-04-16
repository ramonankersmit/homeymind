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
import aiohttp
import async_timeout

# Load environment variables from root .env file
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"
load_dotenv(env_path)

# Set up logging
logging.basicConfig(level=logging.INFO)
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
HOMEY_API_KEY = os.getenv("HOMEY_API_KEY", "")

# Homey API endpoints
HOMEY_API_BASE = f"http://{MQTT_BROKER}"
HOMEY_API_ZONES = f"{HOMEY_API_BASE}/api/manager/zones/zone"
HOMEY_API_DEVICES = f"{HOMEY_API_BASE}/api/manager/devices/device"

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
logger.info(f"Using Homey API at {HOMEY_API_BASE}")

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

# Create FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for state
mqtt_connected = False
mqtt_last_error = None
mqtt_message_count = 0
actual_devices = {}
zones = {}  # Store zones information

# Global session token
session_token = None

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
        # Subscribe to both device and zone topics
        client.subscribe([
            (MQTT_TOPIC, 1),
            (MQTT_REQUEST_TOPIC, 1),
            ("homey/zone/#", 1)  # Add subscription for zones
        ])
        logger.info(f"Subscribed to topics: {MQTT_TOPIC}, {MQTT_REQUEST_TOPIC}, homey/zone/#")
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
    global mqtt_message_count, actual_devices, zones
    try:
        mqtt_message_count += 1
        
        if msg.topic.startswith("homey/devices/"):
            parts = msg.topic.split("/")
            if len(parts) >= 4:
                device_id = parts[2]
                
                if device_id not in actual_devices:
                    actual_devices[device_id] = {
                        "id": device_id,
                        "name": "",
                        "type": "",
                        "deviceType": "",
                        "capabilities": [],
                        "icon": "",
                        "state": {},
                        "zone_id": None
                    }
                
                if len(parts) == 4:
                    if parts[3] == "name":
                        actual_devices[device_id]["name"] = msg.payload.decode().strip('"')
                    elif parts[3] == "zone":
                        zone_id = msg.payload.decode().strip('"')
                        actual_devices[device_id]["zone_id"] = zone_id
                    elif parts[3] == "icon":
                        actual_devices[device_id]["icon"] = msg.payload.decode().strip('"')
                    elif parts[3] == "class":  # Handle class updates
                        device_class = msg.payload.decode().strip('"')
                        actual_devices[device_id]["type"] = device_class
                        # Update icon if not set
                        if not actual_devices[device_id]["icon"]:
                            actual_devices[device_id]["icon"] = device_class
                    elif parts[3] == "type":  # Handle type updates
                        actual_devices[device_id]["deviceType"] = msg.payload.decode().strip('"')
                
                elif len(parts) >= 6 and parts[3] == "capabilities":
                    capability = parts[4]
                    property_name = parts[5]
                    
                    if capability not in actual_devices[device_id]["capabilities"]:
                        actual_devices[device_id]["capabilities"].append(capability)
                    
                    if property_name == "value":
                        try:
                            value = msg.payload.decode().strip('"')
                            if value.lower() == "true":
                                actual_devices[device_id]["state"][capability] = True
                            elif value.lower() == "false":
                                actual_devices[device_id]["state"][capability] = False
                            else:
                                try:
                                    actual_devices[device_id]["state"][capability] = float(value)
                                except ValueError:
                                    actual_devices[device_id]["state"][capability] = value
                        except Exception as e:
                            logger.error(f"Error processing value for {capability}: {e}")
                
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

async def fetch_zones():
    """Fetch zones from Homey API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                headers = {
                    "Authorization": f"Bearer {HOMEY_API_KEY}",
                    "Accept": "application/json"
                }
                async with session.get(HOMEY_API_ZONES, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        zones.clear()
                        for zone_id, zone_data in data.items():
                            zones[zone_id] = {
                                "id": zone_id,
                                "name": zone_data["name"],
                                "devices": []
                            }
                        logger.info(f"Fetched {len(zones)} zones")
                    else:
                        response_text = await response.text()
                        logger.error(f"Failed to fetch zones: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching zones: {str(e)}")

async def fetch_devices():
    """Fetch devices from Homey API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                headers = {
                    "Authorization": f"Bearer {HOMEY_API_KEY}",
                    "Accept": "application/json"
                }
                async with session.get(HOMEY_API_DEVICES, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        for zone in zones.values():
                            zone["devices"] = []
                        
                        for device_id, device_data in data.items():
                            device_class = device_data.get("class", "")
                            device_type = device_data.get("type", "")
                            
                            if device_id not in actual_devices:
                                actual_devices[device_id] = {
                                    "id": device_id,
                                    "name": device_data["name"],
                                    "type": device_class,  # Use class as primary type
                                    "deviceType": device_type,  # Store original type
                                    "zone_id": device_data.get("zone"),
                                    "capabilities": device_data.get("capabilities", []),
                                    "icon": device_data.get("icon", device_class),  # Fallback to class if no icon
                                    "iconObj": device_data.get("iconObj", {}),
                                    "uiIndicator": device_data.get("uiIndicator", ""),
                                    "state": {}
                                }
                            else:
                                actual_devices[device_id].update({
                                    "name": device_data["name"],
                                    "type": device_class,  # Use class as primary type
                                    "deviceType": device_type,  # Store original type
                                    "zone_id": device_data.get("zone"),
                                    "capabilities": device_data.get("capabilities", []),
                                    "icon": device_data.get("icon", device_class),  # Fallback to class if no icon
                                    "iconObj": device_data.get("iconObj", {}),
                                    "uiIndicator": device_data.get("uiIndicator", "")
                                })
                            
                            zone_id = device_data.get("zone")
                            if zone_id and zone_id in zones:
                                if device_id not in zones[zone_id]["devices"]:
                                    zones[zone_id]["devices"].append(device_id)
                        
                        logger.info(f"Fetched {len(data)} devices")
                    else:
                        logger.error(f"Failed to fetch devices: {response.status}")
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")

@app.get("/devices")
async def get_devices():
    """Get all devices grouped by zones."""
    config = load_devices_config()
    demo_devices = config.get("demo_devices", [])
    
    if not mqtt_connected or len(actual_devices) == 0:
        return {
            "zones": [{
                "id": "demo",
                "name": "Demo Zone",
                "devices": demo_devices
            }],
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
    
    zones_with_devices = []
    other_zone = {
        "id": "other",
        "name": "Overig",
        "devices": []
    }
    
    for device_id, device in actual_devices.items():
        device_data = {
            "id": device["id"],
            "name": device["name"],
            "type": device["type"],
            "deviceType": device.get("deviceType", ""),
            "capabilities": device["capabilities"],
            "state": device["state"],
            "zone_id": device["zone_id"],
            "icon": device.get("icon", device["type"]),  # Fallback to type if no icon
            "iconObj": device.get("iconObj", {}),
            "uiIndicator": device.get("uiIndicator", "")
        }
        
        if device["zone_id"] and device["zone_id"] in zones:
            zone_exists = False
            for zone in zones_with_devices:
                if zone["id"] == device["zone_id"]:
                    zone["devices"].append(device_data)
                    zone_exists = True
                    break
            if not zone_exists:
                zones_with_devices.append({
                    "id": device["zone_id"],
                    "name": zones[device["zone_id"]]["name"],
                    "devices": [device_data]
                })
        else:
            other_zone["devices"].append(device_data)
    
    if other_zone["devices"]:
        zones_with_devices.append(other_zone)
    
    return {
        "zones": zones_with_devices,
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
    """Trigger a refresh of devices and zones."""
    try:
        if not mqtt_connected:
            raise HTTPException(
                status_code=503,
                detail="Geen verbinding met MQTT broker"
            )
        
        # Fetch zones and devices from API
        await fetch_zones()
        await fetch_devices()
        
        # Request MQTT updates
        mqtt_client.publish(
            MQTT_REQUEST_TOPIC,
            json.dumps({
                "action": "refresh",
                "timestamp": datetime.now().isoformat()
            }),
            qos=1
        )
        
        return {"status": "success", "message": "Device en zone refresh aangevraagd"}
    except Exception as e:
        logger.error(f"Error refreshing devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """Initialize by fetching zones and devices on startup."""
    logger.info("Starting up backend, fetching initial data...")
    await fetch_zones()
    await fetch_devices()
    logger.info("Startup complete")

# Cleanup MQTT client on shutdown
@app.on_event("shutdown")
def cleanup():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
