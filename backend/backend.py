from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import json
import paho.mqtt.client as mqtt
from queue import Queue
import threading
from datetime import datetime
import time
import os
from dotenv import load_dotenv
import logging
import asyncio
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables and MQTT configuration
MQTT_HOST = os.getenv('HOMEY_HOST')
MQTT_USERNAME = os.getenv('MQTT_USERNAME')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', '60'))

devices = {}
mqtt_client = None
device_updates = Queue()
mqtt_connected = False

def on_mqtt_connect(client, userdata, flags, rc):
    rc_codes = {
        0: "Connection successful",
        1: "Connection refused - incorrect protocol version",
        2: "Connection refused - invalid client identifier",
        3: "Connection refused - server unavailable",
        4: "Connection refused - bad username or password",
        5: "Connection refused - not authorised"
    }
    
    if rc == 0:
        print("\n=== MQTT CONNECTION SUCCESS ===")
        print(f"Connected to {MQTT_HOST}:{MQTT_PORT}")
        print(f"Using username: {MQTT_USERNAME}")
        print("============================\n")
        
        print("Subscribing to topics:")
        topics = [
            "homey/devices/+/name",
            "homey/devices/+/state",
            "homey/devices/+/capabilities/#",
            "homey/devices/+/zone"
        ]
        for topic in topics:
            print(f"  → {topic}")
            client.subscribe(topic)
        print()
    else:
        print("\n=== MQTT CONNECTION FAILED ===")
        print(f"Error: {rc_codes.get(rc, 'Unknown response code')}")
        print(f"Host: {MQTT_HOST}:{MQTT_PORT}")
        print(f"Username: {MQTT_USERNAME}")
        print("==========================\n")

def on_mqtt_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    logger.error("========== MQTT DISCONNECTED ==========")
    logger.error(f"Disconnection reason: {rc}")
    logger.error("Attempting to reconnect...")
    logger.error("=====================================")

def on_mqtt_message(client, userdata, msg):
    try:
        topic_parts = msg.topic.split('/')
        device_id = topic_parts[2]
        
        if device_id not in devices:
            devices[device_id] = {'id': device_id, 'capabilities': {}}
        
        if topic_parts[3] == 'name':
            devices[device_id]['name'] = msg.payload.decode()
        elif topic_parts[3] == 'state':
            devices[device_id]['state'] = msg.payload.decode() == 'true'
        elif topic_parts[3] == 'zone':
            devices[device_id]['zone'] = msg.payload.decode()
        elif topic_parts[3] == 'capabilities':
            capability = topic_parts[4]
            value = msg.payload.decode()
            try:
                value = json.loads(value)
            except:
                pass
            devices[device_id]['capabilities'][capability] = value
        
        device_updates.put(devices[device_id])
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def setup_mqtt():
    global mqtt_client
    
    print("\n=== MQTT CONNECTION PARAMETERS ===")
    print(f"Host      : {MQTT_HOST}")
    print(f"Port      : {MQTT_PORT}")
    print(f"Username  : {MQTT_USERNAME}")
    print(f"Password  : {'*' * 8}")
    print(f"Keepalive : {MQTT_KEEPALIVE}")
    print("===============================\n")
    
    if not all([MQTT_HOST, MQTT_USERNAME, MQTT_PASSWORD]):
        print("\n=== MQTT CONFIG ERROR ===")
        print("Missing required parameters:")
        if not MQTT_HOST: print("  → HOMEY_HOST not set")
        if not MQTT_USERNAME: print("  → MQTT_USERNAME not set")
        if not MQTT_PASSWORD: print("  → MQTT_PASSWORD not set")
        print("=======================\n")
        return False
    
    try:
        print("\n=== ATTEMPTING MQTT CONNECTION ===")
        mqtt_client = mqtt.Client()
        mqtt_client.on_connect = on_mqtt_connect
        mqtt_client.on_message = on_mqtt_message
        mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        print(f"Connecting to {MQTT_HOST}:{MQTT_PORT}...")
        mqtt_client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        mqtt_client.loop_start()
        print("================================\n")
        return True
        
    except Exception as e:
        print("\n=== MQTT CONNECTION ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("=========================\n")
        return False

def get_devices():
    return list(devices.values())

def update_device_capability(device_id, capability, value):
    if device := next((d for d in devices.values() if d['id'] == device_id), None):
        device['capabilities'][capability] = value
        topic = f"homey/devices/{device_id}/capabilities/{capability}/set"
        mqtt_client.publish(topic, json.dumps(value))
        return True
    return False

@app.route('/stream')
def stream():
    def generate():
        while True:
            # Send current device list first
            yield f"data: {json.dumps({'type': 'response', 'content': f'Currently monitoring {len(devices)} devices.'})}\n\n"
            
            # Wait for device updates
            try:
                device = device_updates.get(timeout=30)
                update_msg = f"Device '{device.get('name', device['id'])}' updated"
                yield f"data: {json.dumps({'type': 'response', 'content': update_msg})}\n\n"
            except:
                # Send heartbeat to keep connection alive
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    
    # Process user message and send response
    try:
        # Send initial response
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/clear', methods=['POST'])
def clear_session():
    try:
        # Clear any session-specific data if needed
        return {'status': 'ok'}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/devices')
def get_device_list():
    return {'devices': get_devices()}

@app.route('/devices/<device_id>/capabilities/<capability>', methods=['POST'])
def set_device_capability(device_id, capability):
    data = request.json
    value = data.get('value')
    
    if update_device_capability(device_id, capability, value):
        return {'status': 'ok'}
    return {'error': 'Device not found'}, 404

if __name__ == '__main__':
    setup_mqtt()
    app.run(debug=True) 