import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from app.agents.autogen_manager import AutoGenManager
import yaml
import asyncio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "HomeyMind API"}

# Load configuration
with open(project_root / "config.yaml", "r") as f:
    config = yaml.safe_load(f)

# Initialize AutoGen manager
autogen_manager = AutoGenManager(config)

# Store pending confirmations
pending_confirmations = {}

@app.post("/confirm/{confirmation_id}")
async def confirm_action(confirmation_id: str, confirm: bool):
    """Handle user confirmation for an action."""
    if confirmation_id not in pending_confirmations:
        raise HTTPException(status_code=404, detail="Confirmation not found")
    
    pending_confirmations[confirmation_id].set_result(confirm)
    del pending_confirmations[confirmation_id]
    return {"status": "success"}

@app.get("/chat")
async def chat(request: Request, message: str):
    async def event_generator():
        try:
            async for msg in autogen_manager.process_intent_streaming({"text": message}):
                if msg.get("type") == "complete":
                    yield {
                        "event": "complete",
                        "data": json.dumps({
                            "status": msg.get("status", "success"),
                            "message": msg.get("message", "")
                        })
                    }
                elif msg.get("type") == "confirmation":
                    # Create a new confirmation future
                    confirmation_id = str(datetime.now().timestamp())
                    confirmation_future = asyncio.Future()
                    pending_confirmations[confirmation_id] = confirmation_future
                    
                    yield {
                        "event": "confirmation",
                        "data": json.dumps({
                            "confirmation_id": confirmation_id,
                            "message": msg.get("message", ""),
                            "options": msg.get("options", ["Ja", "Nee"])
                        })
                    }
                    
                    # Wait for user confirmation
                    try:
                        confirmed = await asyncio.wait_for(confirmation_future, timeout=30)
                        if not confirmed:
                            yield {
                                "event": "complete",
                                "data": json.dumps({
                                    "status": "cancelled",
                                    "message": "Actie geannuleerd door gebruiker"
                                })
                            }
                            return
                    except asyncio.TimeoutError:
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "status": "timeout",
                                "message": "Bevestiging verlopen"
                            })
                        }
                        return
                else:
                    yield {
                        "event": "agent_message",
                        "data": json.dumps(msg)
                    }
        except Exception as e:
            # Fallback for errors
            err = {
                "message": f"Er is een fout opgetreden: {str(e)}",
                "role": "agent",
                "isError": True,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            yield {"event": "agent_message", "data": json.dumps(err)}
            yield {
                "event": "complete", 
                "data": json.dumps({
                    "status": "error",
                    "message": str(e)
                })
            }
    
    return EventSourceResponse(event_generator())