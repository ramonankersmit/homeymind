import sys
import os

# Add the project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from app.agents.autogen_manager import AutoGenManager
from typing import AsyncGenerator
import yaml
import asyncio
import json
import logging
from typing import AsyncGenerator
from utils.device_list import KNOWN_DEVICES, update_device_list, DEFAULT_DEVICES

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AutoGen manager
try:
    with open(os.path.join(os.path.dirname(__file__), "../../config.yaml"), "r") as f:
        config = yaml.safe_load(f)
    autogen_manager = AutoGenManager(config)
except Exception as e:
    logger.error(f"Error loading config: {e}")
    config = {}
    autogen_manager = AutoGenManager()

class ChatRequest(BaseModel):
    message: str

async def agent_message_handler(message: dict):
    """Handle new agent messages for SSE."""
    logger.debug(f"Formatting agent message: {message}")
    
    # Determine message type and role
    message_type = 'subagent' if message.get('is_subagent', False) else 'main'
    role = message.get('role', 'agent')
    
    # Format the message for SSE
    formatted_message = {
        "event": "agent_message",
        "id": str(asyncio.get_event_loop().time()),
        "retry": 1000,
        "data": json.dumps({
            "type": message_type,
            "message": message.get("message", ""),
            "role": role,
            "timestamp": message.get("timestamp", "")
        })
    }
    
    logger.debug(f"Formatted message: {formatted_message}")
    return formatted_message

async def complete_handler(data: dict):
    """Handle completion message for SSE."""
    logger.debug(f"Formatting completion message: {data}")
    formatted_message = {
        "event": "complete",
        "id": str(asyncio.get_event_loop().time()),
        "retry": 1000,
        "data": json.dumps(data)
    }
    logger.debug(f"Formatted completion message: {formatted_message}")
    return formatted_message

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        # Format the message as expected by process_intent
        intent_data = {"text": req.message}
        result = await autogen_manager.process_intent(intent_data)
        return {
            "response": result.get("response", "[Geen antwoord]"),
            "agent_data": result
        }
    except Exception as e:
        return {
            "response": f"[Fout]: {str(e)}"
        }

@app.get("/chat")
async def stream_chat(request: Request, message: str):
    """Stream chat responses using SSE."""
    async def event_generator():
        async for partial in autogen_manager.process_intent_streaming({"text": message}):
            if partial.get("type") == "complete":
                yield await complete_handler(partial)
            else:
                yield await agent_message_handler(partial)
    
    return EventSourceResponse(event_generator())

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

@app.get("/devices")
async def get_devices():
    config = load_config()
    
    # Try to update the device list from MQTT
    try:
        logger.info("Updating device list from MQTT...")
        devices = update_device_list(config)
        logger.info(f"Got {len(devices)} devices")
        
        # Format devices for the frontend
        formatted_devices = []
        for device in devices:
            formatted_devices.append({
                "name": device.name,
                "id": device.name.lower().replace(" ", "_"),
                "type": device.type,
                "capabilities": device.capabilities,
                "status": device.status,
                "last_updated": device.last_updated.isoformat()
            })
        
        logger.info(f"Returning {len(formatted_devices)} formatted devices")
        
        # Check if we're using default devices
        if devices == DEFAULT_DEVICES:
            return {
                "devices": formatted_devices,
                "error": {
                    "message": "Kan geen verbinding maken met MQTT broker. Gebruik makend van standaard apparaten.",
                    "details": "Using default devices"
                }
            }
        
        return {"devices": formatted_devices, "error": None}
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return {
            "devices": [], 
            "error": {
                "message": "Kan geen verbinding maken met MQTT broker. Gebruik makend van standaard apparaten.",
                "details": str(e)
            }
        }
