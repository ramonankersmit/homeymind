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

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AutoGen manager
try:
    with open("config.yaml", "r") as f:
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
